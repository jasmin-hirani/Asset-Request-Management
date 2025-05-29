from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError


class AssetRequest(models.Model):
    _name = 'asset.request'
    _description = 'Asset Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc'

    # User who requested
    request_user_id = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user,
                                      readonly=True)
    request_date = fields.Date(string='Request Date', readonly=True)
    request_line_ids = fields.One2many('asset.request.line', 'request_id', string='Products Requested', copy=True)
    reason = fields.Text(string='Reason')

    # Stages for each user group
    internal_stage = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('rejected', 'Rejected'),
        ('done', 'Done'),
    ], string='Internal Stage', default='draft', tracking=True)

    inventory_stage = fields.Selection([
        ('available_request', 'Available Request'),
        ('in_purchase', 'In Purchase'),
        ('purchase_done', 'Purchase Done'),
        ('not_available', 'Not Available'),
        ('rejected', 'Rejected'),
        ('done', 'Done'),
    ], string='Inventory Stage', tracking=True)

    purchase_stage = fields.Selection([
        ('to_purchase', 'To Purchase'),
        ('po_created', 'PO Created'),
        ('rejected', 'Rejected'),
        ('done', 'Done'),
    ], string='Purchase Stage', tracking=True)

    # Computed field to show overall stage (optional)
    stage = fields.Selection(
        selection=lambda self: self._get_overall_stages(),
        string='Overall Stage',
        compute='_compute_stage',
        store=True,
        readonly=True,
    )

    # Helper Fields for User Identification

    ui_is_inventory_user = fields.Boolean(string="UI: Is Inventory User", compute='_compute_ui_user_roles')
    ui_is_purchase_user = fields.Boolean(string="UI: Is Purchase User", compute='_compute_ui_user_roles')
    ui_show_internal_statusbar = fields.Boolean(string="UI: Show Internal SB",
                                                compute='_compute_ui_user_roles')

    @api.depends_context('uid')
    def _compute_ui_user_roles(self):
        is_inventory = self.env.user.has_group('stock.group_stock_user')
        is_purchase = self.env.user.has_group('purchase.group_purchase_user')
        for rec in self:
            rec.ui_is_inventory_user = is_inventory
            rec.ui_is_purchase_user = is_purchase
            rec.ui_show_internal_statusbar = not is_inventory and not is_purchase

    @api.model
    def _get_overall_stages(self):
        # Combine all stages for display or reporting
        return [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('available_request', 'Available Request'),
            ('not_available', 'Not Available'),
            ('in_purchase', 'In Purchase'),
            ('internal_transfer', 'Internal Transfer'),
            ('po_created', 'PO Created'),
            ('done', 'Done'),
            ('rejected', 'Rejected'),
        ]

    @api.depends('internal_stage', 'inventory_stage', 'purchase_stage')
    def _compute_stage(self):
        for rec in self:
            # Simplified example: priority order for stage
            if rec.purchase_stage == 'po_created':
                rec.stage = 'po_created'
            elif rec.purchase_stage == 'to_purchase':
                rec.stage = 'in_purchase'
            elif rec.inventory_stage == 'available_request':
                rec.stage = 'available_request'
            elif rec.internal_stage == 'submitted':
                rec.stage = 'submitted'
            else:
                rec.stage = rec.internal_stage or 'draft'

    # Override create to set default stages
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('request_line_ids'):
                pass
            vals['internal_stage'] = 'draft'
            vals['inventory_stage'] = False
            vals['purchase_stage'] = False
        return super().create(vals_list)

    # Access control helpers
    def _check_user_group(self, group_xml_id):
        return self.env.user.has_group(group_xml_id)

    # Button methods

    # Internal user buttons
    def action_submit(self):
        for rec in self:
            if not rec.request_line_ids:
                raise UserError(_("You must add at least one product to the request before submitting."))
            if rec.internal_stage != 'draft':
                raise UserError("Only draft requests can be submitted.")
            rec.internal_stage = 'submitted'
            rec.inventory_stage = 'available_request'
            rec.request_date = fields.Date.today()

    def action_cancel(self):
        for rec in self:
            if rec.internal_stage == 'done':
                raise UserError("Cannot cancel a done request.")
            rec.internal_stage = 'rejected'
            rec.inventory_stage = 'rejected'
            rec.purchase_stage = 'rejected'

    # Inventory user buttons
    def action_create_internal_transfer(self):
        self.ensure_one()
        if self.inventory_stage != 'available_request':
            raise UserError("Internal Transfer can only be created if product is available.")
        if not self.request_line_ids:
            raise UserError(_("No products selected for internal transfer."))

        move_lines = []
        for line in self.request_line_ids:
            move_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'name': line.product_id.display_name,
            }))

        # FIX: Replace read() with _for_xml_id()
        action = self.env["ir.actions.actions"]._for_xml_id('stock.action_picking_tree_incoming')

        # Ensure the correct view is used (optional but recommended)
        action.update({
            'view_mode': 'form',
            'views': [(self.env.ref('stock.view_picking_form').id, 'form')],
            'context': {
                'default_move_ids_without_package': move_lines,
            },
            # Optional: Clear unwanted keys if needed
            'target': 'new',
        })
        return action

    def action_create_po(self):
        for rec in self:
            rec.inventory_stage = "in_purchase"
            rec.purchase_stage = "to_purchase"

    def action_transfer_done(self):
        for rec in self:
            rec.internal_stage = "done"
            rec.inventory_stage = "done"
            rec.purchase_stage = "done"

    def action_product_unavailable(self):
        for rec in self:
            rec.inventory_stage = "not_available"

    def action_product_received(self):
        for rec in self:
            rec.inventory_stage = "available_request"

    def action_inventory_reject(self):
        for rec in self:
            rec.inventory_stage = 'rejected'
            rec.internal_stage = 'rejected'
            rec.purchase_stage = 'rejected'

    # Purchase user buttons
    def action_purchase_create_po(self):
        for rec in self:
            if rec.purchase_stage != 'to_purchase':
                raise UserError("PO can only be created if in 'To Purchase' stage.")
            if not rec.request_line_ids:
                raise UserError(_("No products selected for Purchase Order."))

            # Prepare order line values for context
            order_lines_vals = []
            for line in rec.request_line_ids:
                order_lines_vals.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.quantity,
                    'product_uom': line.product_uom_id.id or line.product_id.uom_id.id,
                    'price_unit': line.product_id.standard_price,
                    'name': line.product_id.display_name,
                    'date_planned': fields.Date.today(),
                }))

            rec.purchase_stage = 'po_created'

            # Prepare context for the new PO form
            ctx = {
                'default_origin': _('Asset Request for %s') % (rec.request_user_id.name),
                'default_order_line': order_lines_vals,
                'default_company_id': rec.env.company.id,
            }

            # Open the PO form view with prefilled lines, no supplier
            action = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_form_action')
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['context'] = ctx
            action['target']= 'new'
            action.pop('res_id', None)  # Ensure no res_id is set, so it's a new record
            return action

    def action_po_done(self):
        for rec in self:
            if rec.purchase_stage != 'po_created':
                raise UserError("PO Done can only be done if PO is created.")
            rec.purchase_stage = 'done'
            rec.inventory_stage = 'purchase_done'

    def action_purchase_reject(self):
        for rec in self:
            rec.purchase_stage = 'rejected'
            rec.inventory_stage = 'rejected'
            rec.internal_stage = 'rejected'

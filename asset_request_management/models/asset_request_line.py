from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AssetRequestLine(models.Model):
    _name = 'asset.request.line'
    _description = 'Asset Request Line'

    request_id = fields.Many2one('asset.request', string='Asset Request', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', related='product_id.uom_id', readonly=True)


Asset Request Management - In Initial Development

There will be three different operational user groups.
1)Internal user
2)Inventory  user
3)Purchase user 

In module there will be two menus
1) My Requests
2) All Requests (only visible to admin)

For three different user groups there will be different stages.
all stage groups will be visible to only that particular group users.

1) Internal user's stages : Draft, Submitted, Rejected, Done
2) Inventory user's stages : Available Request, In Purchase, Not Available, Rejected, Done
3) Purchase user's stages : To Purchase, PO created, Rejected, Done

Core View of the module will be same but some button and stages will be spacifically visible based on user type. 
Internal user can see only their request but Inventory user should have access of all the requests. Purchase user should have access of request which are came when 
inventory stage is changed to In Purchase.


Fields for the form :

request_user_id (automatically take based on logged in user)
request_date (will be same date when request will be submitted. In Draft stage this field will be empty)
Many2one product selection : product_id, Quantity, Reason (Text field), Buttons (will be visible based on user type)


Buttons :

1) For Internal user
- Submit : Submits request (for internal user stage changes to submitted and and for inventory stage changes to Available Request)
- Cancel : Cancels the request


2) For Inventory user
   Based on availability of products stages in Available or Not Available
 - Create Internal Transfer : When product is in Available, creates an internal transfer to some location (stage changes from Available to Internal Transfer)
 - Create PO : If product is in Not available stage,  create a PO (stage changes from Not Available to In Purchase after creating PO)
 - Reject : for rejecting the request (By clicking stage change to reject as well for Internal user's stage make to Reject)
After successful internal transfer stage should change to Done


3) For Purchase user
  Request in Which PO is created will be in To Purchase stage.
- Create PO : creates a PO for that product (after successful creation, stage will be in PO created)
- PO Done : Make stage to PO Done when Purchase user varifies that product is available
- Reject : To reject the request (For both internal and inventory user it will be in Rejected stage


After submitting request Internal user should not be allowed to make any changes in the request. only inventory and purchase user should have access to change product related info.

User Groups Used
internal_user    base.group_user
inventory_user       stock.group_stock_user
purchase_user     purchase.group_purchase_user


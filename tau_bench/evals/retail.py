# ignore the thinking tool
# ignore transfer to human agents

###
# Here are the rules of evaluation:
# 1. The tool needs to be called for the correct task and with the correct arguments according to its description
# 2. The tool must not contradict any of its requirements
# 3. The tool invoked at this step makes logical sense


## Do we need to track also the original question / task?
# and should we track the previous message history? - it could be from our own agent or from the user

###


EVAL_PROMPT = """
You are tasked with evaluating the correctness of a tool call within an agent workflow aiming to satisfy the following user request: {user_request}
You are given a history of tool calls, the tool call to be evaluated, the tool description, and a scoring rubric that serves as the evaluation standard. Provide a comprehensive feedback on the correctness of the tool call strictly adhering to the scoring rubric. Follow this Yes or No judgement, referring to the scoring rubric. Avoid generating any additional opening, closing, or explanations.

The following tools will cause a change in the database:
(1) modify_pending_order_address: shipping address of the pending order is updated with the new details provided
(2) modify_pending_order_items: items in the pending order are updated with the new details provided
(3) modify_pending_order_payment: payment method of the pending order is updated with the new details provided
(4) modify_user_address: user's address is updated with the new details provided
(5) return_delivered_order_items: items in the delivered order are returned and status changed to "return requested"
(6) exchange_delivered_order_items: items in the delivered order are exchanged and status changed to "exchange requested"

Here are some rules of the evaluation:
(1) You should prioritize evaluating whether the tool is called for the correct task and with the correct arguments according to its description
(2) You should then evaluate whether the tool call satisfies the requirements of the scoring rubric

Your reply should strictly follow this format:
**Reasoning:** <Your feedback>

**Result:** <Yes or No>

Here is the data:

History of tool calls (if any):
```
{history}
```

Tool call:
```
{tool_call}
```

Tool description:
```
{tool_description}
```

Scoring rubric:
{scoring_rubric}
"""


## might need to add information about tools that cause change in the databse
# i.e. modify_pending_order_address: shipping address of the pending order is updated with the new details provided
# i.e. modify_pending_order_items: items in the pending order are updated with the new details provided
# i.e. modify_pending_order_payment: payment method of the pending order is updated with the new details provided
# i.e. modify_user_address: user's address is updated with the new details provided
# i.e. return_delivered_order_items: items in the delivered order are returned and status changed to "return requested"
# i.e. exchange_delivered_order_items: items in the delivered order are exchanged and status changed to "exchange requested"

EVAL_CRITERIA = {
    "calculate": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Single tool call at a time: the tool is not being invoked with other tools at the same time
    - No parallel user response: the model is calling the tool only, without responding to the user at the same time
    - Avoid fabrication: the tool is being called to compute a calculation
    - Do not use before authentication: if the user's query includes or depends on personalized data (e.g., pricing, discounts, etc.), the user is authenticated first before invoking any calculation that includes such data
    - Scoped usage only: the tool is being called only for the purpose of computing a calculation relevant to the retail agent tasks, such as computing total price differences, estimating refunds, determining payment differences in exchanges or modficiations. It is not used for unrelated or general math problems
    - Respect domain restrictions: the tool is not being use outside the scope of: current or potential order totals, item price differences, refund breakdowns]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
    "cancel_pending_order": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Only for pending orders: this tool can only be invoked for orders with status "pending". If order status is "processed" or "delivered" the tool will not work
    - User confirmation: the tool is being called only after the user confirms the cancellation and is informed about the refund timeline (instant if paid by gift card, 5-7 business days if paid by card or PayPal)
    - Inputs are correct: inputs are correct according to the tool description
    - User authentication: the tool is being called only after the user is authenticated
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time
    - Correct context: the order has been checked for cancellation conditions and the user has been informed about the refund timeline]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
    "exchange_delivered_order_items": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Only for delivered orders: this tool can only be invoked for orders with status "delivered". If order status is "pending" or "processed" the tool will not work
    - User confirmation: the tool is being called only after the user confirms the exchange and is informed about the refund timeline (instant if paid by gift card, 5-7 business days if paid by card or PayPal), the payment method user for price differnece, and replacement item details
    - Inputs are correct: inputs are correct according to the tool description
    - One exchange per order: exchange or return can be called only once per order. Once an exchange is made, return/exchange can not be made again for the same order
    - User authentication: the tool is being called only after the user is authenticated
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time
    - No guessing: the tool is not called with guessed item IDs, payment method, or refund amounts]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
    "find_usser_id_by_email": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Purpose: the tool is used to authenticate the user at the start of the workflow
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
    "find_user_id_by_name_zip": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Purpose: the tool is used to authenticate the user at the start of the workflow
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time
    - Inputs are correct: inputs are correct according to the tool description]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
    "get_order_details": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Purpose: the tool is used to retrieve the status and details of an order - often called before actions like cancel, modify, return, or exchange
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time
    - User authentication: the tool is being called only after the user is authenticated
    - Inputs are correct: inputs are correct according to the tool description]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
    "get_product_details": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Purpose: the tool is used to fetch inventory details for a product type. Helps check what variant items are available for a product. Also used to confirm whether an iterm_id offered as an exchange/modification is available under the same product_id
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time
    - User authentication: the tool is being called only after the user is authenticated
    - Inputs are correct: inputs are correct according to the tool description]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
    "get_user_details": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Purpose: the tool is used to retrieve detailed user information about the user's profile, including payment methods or shipping address, and order history
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time
    - User authentication: the tool is being called only after the user is authenticated
    - Inputs are correct: inputs are correct according to the tool description]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
    "list_all_product_types": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Purpose: the tool is used to retrieve a list of all product types in the store or need to access all product IDs
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time
    - User authentication: the tool is being called only after the user is authenticated
    - Inputs are correct: inputs are correct according to the tool description
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
    "modify_pending_order_address": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Only for pending orders: this tool can only be invoked for orders with status "pending". If order status is "processed" or "delivered" the tool will not work
    - User confirmation: the tool is being called only after the user confirms the modification
    - Inputs are correct: inputs are correct according to the tool description
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
    "modify_pending_order_items": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Purpose: modifies items in a pending order to new items of hte same product type (e.g., no switching from a t-shirt to shoes)
    - Only for pending orders: this tool can only be invoked for orders with status "pending". If order status is "processed" or "delivered" the tool will not work
    - User confirmation: the tool is being called only after the user confirms the modification
    - Once per order: the tool can only be called once per order
    - Inputs are correct: inputs are correct according to the tool description
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
    "modify_pending_order_payment": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Only for pending orders: this tool can only be invoked for orders with status "pending". If order status is "processed" or "delivered" the tool will not work
    - User confirmation: the tool is being called only after the user confirms the modification
    - Inputs are correct: inputs are correct according to the tool description
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
    "modify_user_address": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Only for authenticated users: the tool is being called only after the user is authenticated, exists, and has a valid user ID
    - User confirmation: the tool is being called only after the user confirms the modification and its new address
    - Inputs are correct: inputs are correct according to the tool description
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
    "return_delivered_order_items": """[Is the tool called with the correct arguments and satisfies the following requirements?
    - Only for delivered orders: this tool can only be invoked for orders with status "delivered".
    - User confirmation: the tool is being called only after the user confirms the return and is informed about the refund timeline (instant if paid by gift card, 5-7 business days if paid by card or PayPal)
    - Inputs are correct: inputs are correct according to the tool description
    - One tool call at a time: the tool is not being invoked with other tools at the same time, nor is the user being responded to at the same time]
    Yes: All of the above requirements are satisfied
    No: At least one of the above requirements is not satisfied
    """,
}

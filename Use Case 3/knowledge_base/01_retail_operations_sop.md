# Retail Operations SOP

Source ID: RETAIL-SOP-01  
Applies to: Punjab Sports Mart store operations triage, support routing, escalation, analytics, and event evaluation

## Company Context

Punjab Sports Mart is a fictional sports goods retailer headquartered in Jalandhar, Punjab. The company sells cricket bats, balls, protective pads, footballs, hockey sticks, badminton racquets, shoes, fitness accessories, and home fitness equipment through regional stores.

Store associates support individual customers, schools, sports academies, clubs, and tournament buyers. Operational issues can affect customer experience quickly during tournament season, school procurement windows, and weekend rush hours.

## Service Categories

Retail operations requests must be assigned one primary category:

- POS and Payments
- Inventory and Replenishment
- Pricing and Promotions
- Returns and Refunds
- Vendor and Supply Chain
- Product Quality and Safety
- Customer Service
- Other or Security

If a request spans multiple categories, choose the category linked to the immediate risk. For example, "customer injured on treadmill demo unit" is Product Quality and Safety, not Customer Service.

## Priority Rules

P1 means immediate human escalation is required. Use P1 for store-wide POS/payment outage, payment data or credential request, product safety or recall risk, equipment injury risk, unsafe fitness machine, active customer safety issue, or legal/compliance risk.

P2 means high impact but no immediate danger. Use P2 for repeated stock-out of high-demand sports items, vendor short shipment affecting replenishment, pricing error affecting many customers, multiple registers degraded, repeated quality complaints, or urgent manager review.

P3 means routine store issue. Use P3 for one register card reader down, one SKU below reorder point, single shelf label mismatch, standard return guidance, or one-store inventory discrepancy.

P4 means general inquiry. Use P4 for policy questions, reporting requests, or non-urgent operational guidance with no active issue.

## Minimum Triage Fields

For a complete ticket, collect:

- Store ID or location.
- Requester role.
- Issue description.
- Impact scope, such as one customer, one register, one SKU, one department, one store, or multiple stores.
- SKU, product name, register ID, or receipt ID if relevant.
- Time issue started.
- Visible error code, if relevant.

Do not request card numbers, CVV, full customer phone, full customer email, government ID, OTP, passwords, or private account data.

## Escalation Policy

Escalate to a human when:

- Priority is P1.
- The assistant confidence is below 0.60.
- The user asks for restricted data, private customer records, payment data, credentials, contracts, or supplier pricing.
- A policy answer is uncertain or conflicting.
- A requested action requires manager approval, such as refund override, vendor claim, product quarantine, or customer compensation above threshold.

An escalation summary must include category, priority, store, impact scope, policy reason, recommended team, and supporting data if available.

## Citation Rule

Every policy-based answer must cite the source document and section. Acceptable citation examples:

- `01_retail_operations_sop.md#priority-rules`
- `03_inventory_replenishment_policy.md#stock-outs-and-replenishment`

If the assistant cannot find a supporting source, it must say so and avoid inventing policy.

## Analytics Rule

For analytics questions, use the provided CSV data. Do not answer from memory when the answer depends on cases, stores, products, inventory, receipts, vendors, or returns.

For "last 24 hours" and "last 30 days", use the event anchor timestamp from the participant guide: `2026-10-10 12:00:00 IST`.

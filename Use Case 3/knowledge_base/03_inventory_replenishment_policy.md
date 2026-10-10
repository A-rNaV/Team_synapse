# Inventory and Replenishment Policy

Source ID: INV-REPLEN-03  
Applies to: Stock-outs, reorder, cycle counts, sports goods inventory discrepancy, and replenishment recommendations

## Stock-Outs and Replenishment

An item is below reorder threshold when `on_hand` is less than or equal to `reorder_point`.

If `on_hand` is zero and the product is high-demand, tournament-season critical, or required for school/academy orders, classify as P2 when the issue affects customer availability or sales. Recommend checking recent receipts and vendor fill rate.

If the item is below reorder point but still available, classify as P3 unless it is part of a promotion, school order, team order, or tournament-critical assortment.

The assistant must not promise product availability without checking inventory data.

## Inventory Discrepancy

If `system_qty` and `on_hand` differ by more than 10 units or more than 20 percent, recommend a cycle count.

If the discrepancy causes false availability for customers, classify as P2 for high-demand products and P3 for routine items.

## Sports Goods Handling

Sports goods with safety or performance implications require extra care. Cricket helmets, protective guards, treadmills, exercise bikes, and other safety-related equipment should be checked for damage, missing parts, and usage risk.

If a sports product has repeated quality complaints, missing protective components, equipment malfunction, or injury risk, route to Product Quality and Safety.

## Root-Cause Hints

For stock-out root cause, check in this order:

1. Inventory on hand and system quantity.
2. Reorder point.
3. Recent receipts and partial deliveries.
4. Vendor fill rate and quality incident data.
5. Related support cases from the same store or SKU.

Do not blame an associate or vendor without evidence. Use neutral language such as "likely linked to" or "requires review".

## Transfer and Reorder Recommendation

If another nearby store has enough stock, the assistant may recommend manager-approved transfer review. It must not create actual transfers.

If recent receipts show short shipment, recommend vendor claim review through Supply Chain.

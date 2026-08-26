# Deliver

Deliver is currently a truthful Workflow wait boundary. After Release, the
host records that the verified product is ready for later fulfillment and does
not claim manufacture, hands-on QA, packing, carrier handoff, or delivery.

There is intentionally no public Python delivery API yet. The removed receipt
classes described an effect path that no production code or adapter could
execute.

Future physical effects require separate user authorization, host-held
credentials, durable idempotent intents, authenticated reconciliation, and
receipts bound to the exact approved product and Release bytes. Component-owned
contracts may be added here with that implemented path; credential-bearing
adapters belong downstream in `workshop.integrations`.

A Factory page, shipping label, model claim, mocked response, or digital
Playtest is never proof of manufacture or delivery.

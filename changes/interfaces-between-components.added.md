- Spark Make in Contract Mode: a Design Contract (schema 2) now records every
  Interface between Components, with its Kind and the Components it joins
  (ADR 0082). The Manager's shared files hold only what Interfaces need and
  are frozen once their samples pass the print gates; workers start only
  after that freeze, and a later shared change is reported with the
  Components it affects. Each side of a separable Interface checks its
  Keep-out Envelope in its own rounds, and a Coupled Interface such as a gear
  mesh is checked on its two reviewed Components before assembly, sending a
  failure to the one Component the contract says yields. The run report
  lists every Interface and how it was proven.

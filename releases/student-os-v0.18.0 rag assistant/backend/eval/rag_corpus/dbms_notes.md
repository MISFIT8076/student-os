# DBMS — notes

Normalization organizes columns and tables to reduce data redundancy and improve
integrity. First normal form removes repeating groups; second normal form removes
partial dependencies; third normal form removes transitive dependencies on the
primary key.

ACID properties guarantee reliable transactions: atomicity means all-or-nothing,
consistency keeps the database valid, isolation prevents concurrent transactions
from interfering, and durability ensures committed data survives failures.

An index speeds up query lookups by maintaining a sorted structure, often a
B-tree, over one or more columns. Indexes make reads faster but add overhead to
writes and consume extra storage.

A primary key uniquely identifies each row in a table, while a foreign key
references a primary key in another table to enforce referential integrity
between related tables.

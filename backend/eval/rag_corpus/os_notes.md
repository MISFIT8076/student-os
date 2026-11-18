# Operating Systems — notes

Paging is a memory-management scheme that eliminates external fragmentation by
dividing physical memory into fixed-size frames and logical memory into pages of
the same size. The page table maps page numbers to frame numbers, and a
translation lookaside buffer (TLB) caches recent translations to speed up access.

CPU scheduling decides which process runs next on the CPU. Round-robin
scheduling gives each process a fixed time quantum and cycles through the ready
queue, which is good for responsiveness. Shortest-job-first minimizes average
waiting time but requires knowing burst lengths in advance.

A deadlock occurs when a set of processes are each waiting for a resource held by
another, so none can proceed. The four Coffman conditions are mutual exclusion,
hold and wait, no preemption, and circular wait; preventing any one of them
prevents deadlock.

A semaphore is a synchronization primitive with atomic wait and signal
operations used to control access to shared resources and avoid race conditions
in concurrent programs.

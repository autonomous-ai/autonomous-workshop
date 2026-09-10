Include the macOS Python framework binary, launcher symlink traversal, and
linked standard-library dependency directories in the read-only native runtime
boundary. Recognize the exact previous runtime policy so a blocked session can
resume without changing its identity or allowing host-state access.

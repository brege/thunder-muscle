## Thunderbird Profile Preparation

1. Settings → Search "Indexing" →
   - [✓] "Enable Global Search and Indexer"
   - "Message Store Type for new accounts": Select **File per folder (mbox)**
3. Tools → Activity Manager - wait for indexing to complete
5. Copy Thunderbird's profile folder (e.g. ~/.thunderbird/) to a location of your choice
   ``` bash
   cp ~/.thunderbird/*.default-release assets/
   ```
If you want to run directly on the in situ profile, Thunderbird must be closed first.

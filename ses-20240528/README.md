- It was ran from Yarik's laptop, not reproiner.  Failed to install psychopy in a virtualenv on reproiner -- might need wx etc libraries
- Laptop clock is not entirely in sync :-/

    ❯ date --iso-8601=ns | tr "\n" "\t" ; for h in reproiner birch localhost; do ssh $h 'date --iso-8601=ns | tr "\n" "\t" ; hostname' & done; sleep 3;
    2024-05-28T11:50:40,131809493-04:00	
    2024-05-28T11:50:40,168054275-04:00	bilena
    2024-05-28T11:50:40,777833551-04:00	reproiner
    2024-05-28T11:50:40,813447469-04:00	Birch-4115966

so over 600ms off. I am installing ntpsec now

- There should be two last runs of data and logs and videos

 We did restart the psychopy script  a few times though

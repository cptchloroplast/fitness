graph LR
    wahoo[Wahoo]-->|Email|worker[Cloudflare Worker]
    worker-->|HTTP|function[Google Cloud Run Function]
    function-->|HTTP|garmin[Garmin API]
    secrets[Google Cloud Secret Manager]---|Garmin Token|function
    service_account[Google Cloud Service Account]---|Private Key|worker
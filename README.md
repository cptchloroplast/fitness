# Wahoo to Garmin Sync

Check out [my blog post](https://ben.okkema.org/posts/wahoo-to-garmin-sync) for a more spirited write up and other weird stuff.

## Introduction

Wahoo offers many [native integrations](https://support.wahoofitness.com/hc/en-us/articles/23022859474962-Wahoo-App-Partners) for syncing data with other platforms, however, there is not such integration for [Garmin Connect](https://connect.garmin.com/). This is problematic for cyclists who wish to continue to track rides in Connect, either due to a switch from Garmin to Wahoo head units or those who use additional Garmin devices such as a smart watch. This repository contains an opionated solution to address this by leveraging the Wahoo native email integration, [Cloudflare Email Workers](https://developers.cloudflare.com/email-routing/email-workers/) and [Google Cloud Run Functions](https://cloud.google.com/run/docs/runtimes/python). 

## [Architecture](./docs/architecture.md)

Wahoo sends an email containing a link to the workout file to an address that is bound to an Email Worker

The Worker executes the following steps:
  - Parse the raw RFC822 email message 
  - Extract the link from the HTML body using regex
  - Download the `.fit` workout file from into memory
  - Send file to the Function as `application/x-www-form-urlencoded` data in a HTTP request

The Function then executes the following steps:
  - Connect to Garmin API using provided credentials
  - Upload the attached workout file to the API


## Security Considerations

The Worker validates that the email is coming from the correct address used by Wahoo. 

The Worker uses a Service Account that is authorized to invoke the Function and authenticates with Google Cloud by using a private key. 

Garmin credentials are generated locally using a [script](./scripts/login.py) and then provided to the Function using Google Cloud Secret Manager. 

Infrastructure is provisioned by Terraform using the managed remote backend for storing variables and secrets.

## Credits

Big thanks to the contributors of [garth](https://github.com/matin/garth) for making interactions with the Garmin API a snap!
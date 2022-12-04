# Akamai CLI: MFA<!-- omit in toc -->

Welcome to the Akamai MFA package for Akamai CLI, *cli-mfa* for short.  
For more information about Akamai MFA, see https://www.akamai.com/mfa

## Table of contents<!-- omit in toc -->

- [Pre-requisites](#pre-requisites)
  - [Akamai CLI](#akamai-cli)
  - [Python 3](#python-3)
- [Getting started](#getting-started)
  - [API Credentials to interact with Akamai MFA configuration](#api-credentials-to-interact-with-akamai-mfa-configuration)
  - [API Credentials to fetch authentication events](#api-credentials-to-fetch-authentication-events)
  - [Advanced usage](#advanced-usage)
- [Command examples](#command-examples)
  - [General information and inline help](#general-information-and-inline-help)
  - [Fetch authentification events](#fetch-authentification-events)
  - [MFA identity management (users, groups...)](#mfa-identity-management-users-groups)
- [Streaming Akamai MFA events to a SIEM](#streaming-akamai-mfa-events-to-a-siem)
- [Support](#support)


## Pre-requisites

### Akamai CLI

Make sure your first have Akamai CLI installed on your machine.

We support a wide variety of platform: Windows, Mac, Linux, container...
Download the CLI from [https://techdocs.akamai.com/developer/docs/about-clis](https://techdocs.akamai.com/developer/docs/about-clis)

For more information, please visit the [Getting Started video](https://www.youtube.com/watch?v=BbojoaTTT3A).

### Python 3

Beyond Akamai CLI pre-requisites, `cli-mfa` requires Python 3.7 or greater on your system, as well as Python Package manager `pip`.

You can verify by opening a shell and type `python --version` and `pip --version`
If you don't have Python on your system, go to [https://www.python.org](https://www.python.org).

## Getting started

`cli-mfa` allows to interact with different Akamai MFA components:

- Configuration, to manage your various Akamai MFA setup (users, group, policy, ...)
- Logging Integration, to pull authentication events

Each comes with its set of API credentials, so depending on the operation you're looking for, you may need one or two sets of credentials. Instructions provided below.

### API Credentials to interact with Akamai MFA configuration 

For any other *cli-mfa* operations you will need you Akamai {OPEN} credentials.

In [Akamai Control Center](https://control.akamai.com), make sure you create an API user 
with the _Akamai MFA_ (`/amfa`) with `READ-WRITE` or `READ` permission.  
If you choose `READ`, *cli-mfa* will be allowed to perform only API HTTP `GET` class.

Upon user credential creation, you'll get a `.edgerc` file with 4 parameters.

The value of the parameter is a integer you can obtain by navigating in Akamai Control Center: 

Example of `.edgerc` file:
```
[default]
client_secret = client-secret-goes-here
host = akab-xxxx.luna.akamaiapis.net
access_token = your-access-token
client_token = your-client-token
```

### API Credentials to fetch authentication events

To be able to use the command `akamai mfa events` you'll need to configure an logging integration in [Akamai Control Center](https://control.akamai.com).

- Use left navigation (mega menu) and select Enterprise Center
- Open **MFA** > **Integrations**
- Click on (+) to add a new integration
- Select **Logging**
- Set a name, e.g. *cli-mfa*
- Click and **Save and Deploy**

Now, copy both **Integration ID** and **Signing Key**

Add them both into your `~/.edgerc` file, either in the [default] section or one of your choice:

```
[default]
mfa_integration_id = app_12345abcdef
mfa_signing_key = some-random-key
```

### Advanced usage

If you are working with multiple tenants, create a different integration credentials in each tenant and place them into different section of the `.edgerc` file.

To verify your configuration, you may use `akamai mfa info`, see example below.

## Command examples

### General information and inline help

General help:
```
% akamai mfa --help
```

Help about fetching Akamai MFA authentication events:
```
% akamai mfa event --help
```

Information about your *cli-mfa* configuration
```
% akamai mfa info
```
output:
```json
{
    "general": {
        "cli-mfa_version": "1.2.3",
        "python": "3.8.15 (default, Oct 11 2022, 21:52:37)",
        "akamai_cli": "1.5.1",
        "edgerc_file": "~/.edgerc",
        "edgerc_section": "default"
    },
    "amfa-logging-api": {
        "mfa_integration_id": "app_12345abcdef",
        "mfa_signing_key": "************************abcd"
    },
    "akamai-open-api": {
        "host": "akab-xxxx.luna.akamaiapis.net",
        "access_token": "your-access-token",
        "client_token": "your-client-token",
        "client_secret": "**********client-secret-goes-here",
        "contract_id": "1-123-456"
    }
}
```

Version of `cli-mfa`

```
% akamai mfa version
1.2.3
```

### Fetch authentification events

Try to pull MFA security events with the following examples.
When ``--start`` is omitted, start is set to 5 minutes ago.
When ``--end`` is omitted, end takes now minutes 30 seconds.

```
% akamai mfa event
```

### MFA identity management (users, groups...)

List of all the users:
```
% akamai users list
```

## Streaming Akamai MFA events to a SIEM

Akamai MFA comes with a native Splunk App for Splunk Enterprise you can find on [SplunkBase](https://splunkbase.splunk.com/app/5490/).

If you are using a different Splunk edition or a different SIEM, check out our [Unified Log Streamer (ULS)](https://github.com/akamai/uls) repository.

## Support

`cli-mfa` is provided as-is and it is not supported by Akamai Support.
To report any issue, feature request or bug, please open a new issue into the [GitHub Issues page](https://github.com/akamai/cli-mfa/issues)

We are encouraging developers to create a pull request.


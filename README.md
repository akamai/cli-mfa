# Akamai CLI: MFA

Welcome to the Akamai MFA module for Akamai CLI.
For more information about Akamai MFA, see https://www.akamai.com/mfa

## Table of contents<!-- omit in toc -->

- [Akamai CLI: MFA](#akamai-cli-mfa)
  - [Pre-requisites](#pre-requisites)
    - [Akamai CLI](#akamai-cli)
    - [Python](#python)
  - [Getting started](#getting-started)
  - [Field documentation](#field-documentation)
  - [Command examples](#command-examples)
  - [Streaming Akamai MFA events to a SIEM](#streaming-akamai-mfa-events-to-a-siem)
  - [Support](#support)


## Pre-requisites

### Akamai CLI

Make sure your first have Akamai CLI installed on your machine.

We support a wide variety of platform: Windows, Mac, Linux, container...
Download the CLI from [https://techdocs.akamai.com/developer/docs/about-clis](https://techdocs.akamai.com/developer/docs/about-clis)

For more information, please visit the [Getting Started video](https://www.youtube.com/watch?v=BbojoaTTT3A).

### Python

Beyond Akamai CLI pre-requisites, `cli-mfa` requires Python 3.6 or greater on your system, as well as `pip`.

You can verify by opening a shell and type `python --version` and `pip --version`
If you don't have Python on your system, go to [https://www.python.org](https://www.python.org).

## Getting started

You'll need to configure an logging integration in [Akamai Control Center](https://control.akamai.com).

- Use left navigation (mega menu) and select Enterprise Center
- Open **MFA** > **Integrations**
- Click on (+) to add a new integration
- Select **Logging**
- Set a name, e.g. *cli-mfa*
- Click and **Save and Deploy**

Now, copy both Integration ID and Signing Key

Add them both into your `~/.edgerc` file, either in the [default] section or one of your choice:

```
[default]
mfa_integration_id = app_12345abcdef
mfa_signing_key = some-random-key
```

If you are working with multiple tenants, create a different integration credentials in each tenant and place them into different section of the `.edgerc` file.

## Field documentation

Output is using JSON formatting, you'll find all the details about each attribute on our dedicated 
section on [techdocs.akamai.com](https://techdocs.akamai.com/mfa/docs/field-sequence)

## Command examples

Inline general help
```
% akamai mfa --help
```

Inline help for auth event
```
% akamai mfa event --help
```

Try to pull MFA security events with the following examples.
When ``--start`` is omitted, start is set to 5 minutes ago.
When ``--end`` is omitted, end takes now minutes 30 seconds.

```
% akamai mfa event
```

Version of `cli-mfa`

```
% akamai mfa version
1.2.3
```

## Streaming Akamai MFA events to a SIEM

Akamai MFA comes with a native Splunk App for Splunk Enterprise you can find on [SplunkBase](https://splunkbase.splunk.com/app/5490/).

If you are using a different Splunk edition or a different SIEM, check out our [Unified Log Streamer (ULS)](https://github.com/akamai/uls) repository.

## Support

`cli-mfa` is provided as-is and it is not supported by Akamai Support.
To report any issue, feature request or bug, please open a new issue into the [GitHub Issues page](https://github.com/akamai/cli-mfa/issues)

We are encouraging developers to create a pull request.


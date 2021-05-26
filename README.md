# Akamai CLI: MFA

Welcome to the MFA module for Akamai CLI.

## Table of contents<!-- omit in toc -->

- [Akamai CLI: MFA](#akamai-cli-mfa)
  - [Getting started](#getting-started)
  - [Field documentation](#field-documentation)
  - [Command examples](#command-examples)
  - [Streaming Akamai MFA events to a SIEM](#streaming-akamai-mfa-events-to-a-siem)
  - [Support](#support)

## Getting started

You'll need to configure an logging integration in [Akamai Control Center](https://control.akamai.com).

- Use left navigation (mega menu) and select Enterprise Center
- Open **MFA** > *Integrations***
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

If you are working with multiple tenants, create a different integration credentials in each tenant and place them into different section of the `edgerc` file.

## Field documentation

Output is using JSON formatting, you'll find all the details about each attribute on our dedicated section on [learn.akamai.com](https://learn.akamai.com/en-us/webhelp/enterprise-mfa/akamai-mfa-logs-from-splunk-application/GUID-0F17296F-90F3-483E-AFDE-F98FBC51A8AC.html)

## Command examples

Try to pull MFA events with the following examples.

For Authentication events:

```
% akamai mfa event auth
```

For Policy events:
```
% akamai mfa event policy
```

Version of `cli-mfa`

```
% akamai mfa version
1.2.3
```

## Streaming Akamai MFA events to a SIEM

Akamai MFA comes with a native Splunk App you can find on [SplunkBase](https://splunkbase.splunk.com/app/5490/).

If you are using a different SIEM, we are working on universal solution, please check out our [Unified Log Streamer (ULS)](https://github.com/akamai/uls) repository.

## Support

`cli-mfa` is provided as-is and it is not supported by Akamai Support.
To report any issue, feature request or bug, please open a new issue into the [GitHub Issues page](https://github.com/akamai/cli-mfa/issues)

We are encouraging developers to create a pull request.


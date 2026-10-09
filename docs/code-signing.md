# Code signing

Releases are signed through [SignPath Foundation](https://signpath.org) (free for open source).
The rules we agreed to are in the README's [Code signing policy](../README.md#code-signing-policy).

## What gets signed, and when

Only when a merge into `main` publishes a **new version** (see [release.yml](../.github/workflows/release.yml)):

1. CI builds and smoke-tests `converter.exe` as usual.
2. `converter.exe` is sent to SignPath → **you approve the request** → the signed exe comes back.
3. `Setup.exe` is rebuilt around the signed exe and sent to SignPath → **you approve again**.
4. The workflow checks both signatures, runs the full installer test on the signed installer and publishes the release.

Pull requests and merges without a version change are never signed.
Until SignPath is configured (below), releases are published unsigned with a warning in the run log.

Each request waits up to 3 hours for approval. If it times out or you reject it, fix the cause and use **Re-run failed jobs** on the run.

## One-time setup (after SignPath approves the project)

### 1. In SignPath (app.signpath.io)

1. Turn on multi-factor authentication for your SignPath account. It's mandatory.
2. Open the project (slug `PocketConverter`, or note the slug they gave it) and make sure the **Trusted Build System "GitHub.com"** is linked to it. SignPath usually sets this up during onboarding.
3. Under **Artifact Configurations**, create two configurations with exactly these **slugs** and contents:

   Slug **`app`**:
   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <artifact-configuration xmlns="http://signpath.io/artifact-configuration/v1">
     <parameters>
       <parameter name="version" required="true" />
     </parameters>
     <zip-file>
       <pe-file path="converter.exe" product-name="PocketConverter" product-version="${version}">
         <authenticode-sign />
       </pe-file>
     </zip-file>
   </artifact-configuration>
   ```

   Slug **`installer`**:
   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <artifact-configuration xmlns="http://signpath.io/artifact-configuration/v1">
     <parameters>
       <parameter name="version" required="true" />
     </parameters>
     <zip-file>
       <pe-file path="PocketConverterSetup-${version}.exe" product-name="PocketConverter" product-version="${version}">
         <authenticode-sign />
       </pe-file>
     </zip-file>
   </artifact-configuration>
   ```

   The `product-name` / `product-version` restrictions are required by SignPath Foundation. `build.ps1` and `installer/installer.iss` set exactly these values in both files.
4. Note the **signing policy** slug, normally `release-signing`, and make sure you are its **approver**.
5. Create an **API token** for a user that is a **submitter** on that signing policy (a dedicated CI user if SignPath offers one). Copy it; you only see it once.
6. Copy your **Organization ID** (shown in the organization settings / URL).

### 2. In GitHub (repository → Settings → Secrets and variables → Actions)

| Kind | Name | Value |
|------|------|-------|
| Secret | `SIGNPATH_API_TOKEN` | the API token from step 5 |
| Variable | `SIGNPATH_ORGANIZATION_ID` | the organization ID from step 6 |
| Variable (only if different) | `SIGNPATH_PROJECT_SLUG` | default `PocketConverter` |
| Variable (only if different) | `SIGNPATH_SIGNING_POLICY_SLUG` | default `release-signing` |

That's all; the workflows pick these up automatically.

## Releasing a signed version

1. On `development`: set `__version__` in `converter_app/__init__.py` (e.g. `2.0.1`) and write `docs/release-notes/v2.0.1.md`.
2. Pull request `development` → `main`, wait for green CI, merge.
3. Watch the **Release** run in the Actions tab. When it reaches *Sign converter.exe*, approve the request in SignPath (you also get an e-mail); then the same for *Sign Setup.exe*.
4. The release appears under Releases. Check it: right-click the downloaded `.exe` → **Properties → Digital Signatures** should list *SignPath Foundation*.

## Antivirus false positives

After every release, submit the files to Microsoft so Defender learns they're clean:

1. Go to <https://www.microsoft.com/en-us/wdsi/filesubmission>, choose **Software developer**, sign in with a Microsoft account (lets you track the result).
2. Product: **Microsoft Defender Antivirus** (or **Microsoft Defender SmartScreen** for the "Windows protected your PC" warning).
3. The limit is **50 MB per file**, so the 96 MB installer can't be uploaded. Upload `C:\Program Files\PocketConverter\converter.exe` instead, plus any other single file Defender reports by name.
4. "What do you believe this file is?" → **Incorrectly detected as malware/malicious**. Detection name: the name Defender shows, or `SmartScreen: unrecognized app`.
5. Additional information, for example:
   > Open-source file converter (https://github.com/N1ck6/PocketConverter), built from public source by GitHub Actions and signed through SignPath Foundation. Release: https://github.com/N1ck6/PocketConverter/releases/latest
6. Priority **Medium**. The answer usually arrives within a few days by e-mail and in *Submission history*.

For other antivirus vendors, check the installer on <https://www.virustotal.com> and use each flagging vendor's false-positive form.

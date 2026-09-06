# Security policy

Only the latest release receives security fixes. Version 0.2.0 supports only
MSI Thin GF63 12VE with EC firmware 16R8IMS1.107.

Please do not publish a vulnerability or an unredacted EC dump in a public
issue. Use GitHub private vulnerability reporting:

https://github.com/4ykutG/fan-driver/security/advisories/new

Do not include passwords, tokens or other personal data.

New model requests must first establish support in upstream `msi-ec`. Patches
that bypass the DMI/firmware allowlist, disable firmware thermal protection,
change power profiles, MSI Shift, VBIOS limits or write raw EC addresses will
not be accepted.

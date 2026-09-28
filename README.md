# docextract Helm chart repository

This branch is a Helm chart repository (not application source — see `main` for that),
served over HTTP via GitHub Pages.

```bash
helm repo add docextract https://santosh-oc.github.io/docextract/
helm repo update
helm install docextract docextract/docextract
```

Regenerate after packaging a new chart version:

```bash
helm package charts/docextract -d /path/to/this/branch/checkout
helm repo index /path/to/this/branch/checkout --url https://santosh-oc.github.io/docextract/
```

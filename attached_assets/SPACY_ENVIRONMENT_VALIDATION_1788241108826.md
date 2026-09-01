# spaCy Environment Validation

## Root cause found

The repository dependency configuration correctly uses `pymupdf`:

```text
pymupdf
```

There is no `fitz` entry in `requirements.txt`, `pyproject.toml`, `uv.lock`, Poetry configuration, or the relevant `.replit` Nix package list.

The existing application imports PyMuPDF using its supported Python import name:

```python
import fitz
```

That import is supplied by the installed `PyMuPDF` distribution. Verification showed:

- `PyMuPDF==1.27.2.2` is installed;
- `import fitz` succeeds;
- no separately installed `fitz` distribution exists.

The package manager nevertheless appends the import name as a separate PyPI requirement whenever spaCy installation is requested:

```text
pip install spacy fitz
```

and, when PyMuPDF is also explicitly provided:

```text
pip install spacy pymupdf fitz
```

The deprecated `fitz` distribution is deactivated and fails before spaCy can be installed:

```text
Package 'fitz' has been deactivated and cannot be installed.
Please install 'pymupdf' instead.
```

The issue is therefore in the package-manager dependency mapping/resolution layer, not in the repository's declared PDF dependency.

## Files changed

Only this validation document was created:

- `docs/SPACY_ENVIRONMENT_VALIDATION.md`

No application source, dependency declaration, OCR code, validation logic, extraction logic, confidence logic, UI, database, schema, demo data, or workflow configuration was changed for this environment task.

## Dependency correction made

No correction was applied because the repository already has the correct dependency:

```text
pymupdf
```

The deprecated `fitz` package was not installed, and no unsupported alias, shim, manual site-package copy, or application-import rewrite was introduced.

The minimum spaCy installation was attempted through the supported package-management path twice:

1. `spacy`
2. `spacy` with explicit `pymupdf`

Both attempts failed because `fitz` was appended by the resolver.

## Installed spaCy version

None. spaCy is not installed.

No pretrained spaCy model, including `en_core_web_sm`, was downloaded.

## PyMuPDF / fitz verification

The existing PyMuPDF installation remains available:

```text
PyMuPDF==1.27.2.2
```

The existing import succeeds:

```python
import fitz
```

## `spacy.blank("en")` verification

Not available because `import spacy` fails with:

```text
ModuleNotFoundError: No module named 'spacy'
```

Consequently, `spacy.blank("en")` could not be executed.

## App startup verification

The existing Streamlit workflow remains running successfully after the failed package attempts.

The app continues to use the prior environment and behavior. No application logic was changed.

Existing browser console chart warnings remain unrelated to this environment task; no application traceback or startup failure was observed.

## Recommended next option

The package-manager resolver needs a supported mapping from the import name `fitz` to the distribution `pymupdf`, or an equivalent configuration that prevents import-name inference from adding deprecated `fitz`.

Once that resolver issue is corrected, install only spaCy and verify:

```python
import fitz
import spacy

nlp = spacy.blank("en")
```

Changing application imports, adding a manual shim, bypassing the package firewall, or replacing spaCy with another NLP library would be a larger or riskier change and was intentionally not attempted.

## Final status

**Still blocked.**

PyMuPDF/`fitz` works as before, the Streamlit app still starts, and the application remains unchanged. The environment is not yet ready for P2-B because spaCy could not be installed cleanly.
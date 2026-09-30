---
pretty_name: Synthetic Toy Object Detection Dataset
license: mit
task_categories:
  - object-detection
tags:
  - synthetic
  - image
  - coco
  - mlcroissant
---

# Synthetic Toy Object Detection Dataset

6 deterministic PNG images and COCO 1.0 annotations used to test the reference release pipeline without customer data or external downloads.

## Intended use

- Exercise ingestion, annotation validation, immutable release publishing and presigned delivery.
- Provide a small fixture for unit and integration tests.
- Demonstrate the release manifest, dataset card and Croissant metadata contracts.

This dataset is not suitable for model training, benchmarking, fairness evaluation or production quality assessment.

## Composition and provenance

- Modality: image.
- Files: 6 PNG images and one COCO annotation file.
- Generation: deterministic local shapes produced by `cvat_b2_pipeline.synth`; no real people, customer data or downloaded source material.
- Annotations: generated with the images and validated for category references, bounding boxes, coverage and checksums.
- Release version: `v1`.

## Rights and sensitive data

The fixture is distributed under the [MIT license](https://spdx.org/licenses/MIT.html). It contains no intentionally collected personal information, biometric identifiers or licensed third-party media.

## Machine-readable metadata

- [Croissant JSON-LD](croissant.json)
- `manifest.json`, written last by the publisher, supplies the release identity and per-file integrity data.

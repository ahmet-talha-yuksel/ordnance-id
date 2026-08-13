# Scope and Safety Limits

## What the system is

ORDNANCE-ID is a research decision-support prototype for humanitarian mine-action and EOD
training contexts. It uses photographs to suggest probabilistic ordnance-family candidates,
shows supporting evidence, and can abstain when image quality or confidence is insufficient.
Every result must remain subject to assessment by qualified personnel.

## What the system is not

The system is not an operational identification authority. It does not identify an exact model
or type with certainty, declare an object safe, or provide instructions for handling, moving,
disarming, neutralising, destroying, or otherwise interacting with suspected ordnance. It is not
designed for targeting, weapon employment, combat operations, or autonomous decision-making.

## Design consequences

- **Fixed safety templates:** Safety-protocol text comes from reviewed, versioned templates, not
  generated model prose.
- **Abstention:** Results below the configured confidence threshold are withheld rather than
  converted into a forced prediction.
- **Quality gate:** Inadequate, ambiguous, or incomplete imagery is rejected before
  classification.
- **Traceability:** Inputs, model/configuration versions, retrieved references, intermediate
  evidence, confidence, and template versions must be auditable.
- **Family-level language:** Outputs remain probabilistic and at ordnance-family level; they must
  communicate uncertainty explicitly.

## Intended users

The intended users are researchers, trainers, and appropriately qualified mine-action or EOD
professionals evaluating decision-support concepts. The prototype is not intended for the public
to assess or approach suspected hazardous objects.

## Ethical position

Human safety and harm reduction govern the project. Target selection, weapon construction or use,
and advice that enables interaction with explosive hazards are outside scope. Dataset and model
choices must support humanitarian objectives, lawful research, provenance, and accountable human
oversight.


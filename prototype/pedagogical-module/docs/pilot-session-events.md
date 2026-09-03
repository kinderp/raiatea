# Pilot session events

Issue: #95  
Parent: #93

This document defines one closed local non-identifying incident record for a supervised Raiatea pilot.

The record contains only release version, supervised-checklist digest, severity, category, stop requirement, canonical handling actions and resolution status. Allowed severities are low, medium, high and critical. Allowed categories are runtime, privacy-boundary, content, accessibility and supervision.

Critical severity, every privacy-boundary event and an unsafe runtime event require immediate stop. Actions come from a closed ordered vocabulary and contain no free text.

Names, learner answers, class or school identifiers, timestamps, narrative, device details, accounts, network destinations and contact data are forbidden.

The tool will support explicit create, validate, export and delete operations over regular deterministic JSON files with no-replace writes. Delete requires structural validation.

Release gating and final decisions remain #96–#97. Tests cover closed fields, stop rules, canonical values, lifecycle safety, privacy exclusions and deterministic serialization.
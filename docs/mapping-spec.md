# Mapping Spec

This document describes how to create and use mapping specifications for `edi-cli`.

## Overview

A mapping specification defines how an EDI transaction set is structured, including its loops, segments, and elements. These specifications are used by the parser to correctly interpret the EDI data.

## Creating a New Mapping

To create a new mapping, you will need to define the structure of the transaction set in a JSON file. The file should be placed in the `packages/core/x12/schemas` directory.

The mapping file should contain a `schema` object with the following properties:

*   `delimiters`: An object defining the segment, element, and sub-element delimiters.
*   `segments`: An object defining the segments in the transaction set.

### Example

```json
{
  "schema": {
    "delimiters": {
      "segment": "~",
      "element": "*",
      "sub_element": ":"
    },
    "segments": {
      "ISA": {
        "name": "Interchange Control Header",
        "elements": [
          {"name": "AuthorizationInformationQualifier", "type": "string"},
          // ...
        ]
      },
      // ...
    }
  }
}
```

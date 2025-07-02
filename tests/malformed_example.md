# Example Report

This is an example of malformed markdown that typically causes the "bad hierarchy level in row 1" error.

## Data Analysis

| Metric | Q1 | Q2 | Q3 | Q4
Sales | $100K | $120K | $110K | $130K |
| Growth | 5% | 20% | -8% | 18%
Revenue | $500K | $600K | $550K | $650K |

#### Immediate jump to level 4 heading

This heading hierarchy jump can cause issues.

| Task | Status | Owner
| Setup | Complete | Alice |
Testing | In Progress | Bob |
| Deploy | Pending | Charlie |

##### Another level jump

More content with formatting issues:

- Item without space
*Another item without space
1.Numbered item without space

```code
Malformed code block


```

## Summary

The above content contains multiple formatting issues that typically cause PDF conversion errors:

1. Missing table header separators (---|---|---)
2. Inconsistent pipe separators in table rows  
3. Heading level jumps (## directly to ####)
4. List items without proper spacing
5. Malformed code blocks

These issues should be automatically fixed by the sanitization system. 
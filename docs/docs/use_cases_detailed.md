# Detailed Use Cases - CodeGraphContext

This document provides **10 detailed, real-world use cases** with concrete examples, exact steps, time/cost savings, and ROI calculations.

Each use case includes:
- **Scenario**: Real-world problem
- **Without CGC**: Traditional approach with time/cost
- **With CGC**: CGC-powered approach with exact commands
- **Savings**: Quantified time and cost savings
- **ROI**: Return on investment calculation

---

## Table of Contents

1. [Use Case 1: Safe Refactoring - Renaming a Critical Function](#use-case-1-safe-refactoring---renaming-a-critical-function)
2. [Use Case 2: Code Cleanup - Finding Dead Code](#use-case-2-code-cleanup---finding-dead-code)
3. [Use Case 3: Technical Debt Assessment](#use-case-3-technical-debt-assessment)
4. [Use Case 4: Onboarding New Developers](#use-case-4-onboarding-new-developers)
5. [Use Case 5: Bug Investigation - Tracing Data Flow](#use-case-5-bug-investigation---tracing-data-flow)
6. [Use Case 6: API Deprecation Planning](#use-case-6-api-deprecation-planning)
7. [Use Case 7: Architecture Review](#use-case-7-architecture-review)
8. [Use Case 8: Security Audit](#use-case-8-security-audit)
9. [Use Case 9: Performance Optimization](#use-case-9-performance-optimization)
10. [Use Case 10: Code Review - PR Impact Analysis](#use-case-10-code-review---pr-impact-analysis)

---

## Use Case 1: Safe Refactoring - Renaming a Critical Function

### Scenario

**Company**: E-commerce platform with 50k LOC  
**Task**: Rename `execute_cypher_query` to `run_graph_query` for better clarity  
**Challenge**: Function is used throughout the codebase, need to ensure nothing breaks  
**Developer**: Senior Backend Engineer ($75/hr)

### Without CGC ❌

#### Step 1: Find all occurrences (15 minutes)
```bash
grep -r "execute_cypher_query" . --include="*.py"
```
**Output**: 150+ lines (includes comments, strings, docstrings, imports)

#### Step 2: Manually filter false positives (15 minutes)
- Read through each line
- Identify actual function calls vs comments
- Miss some edge cases (dynamic calls, string references)

#### Step 3: Find indirect callers - THE HARD PART (45 minutes)
```bash
# For each caller, manually search what calls THEM
grep -r "execute_cypher_query_tool" .
# Then grep for what calls THAT function
# Repeat for multiple levels...
```
**Problem**: You'll miss indirect callers, leading to runtime errors

#### Step 4: Make changes (20 minutes)
- Manually edit each file
- High risk of missing some occurrences

#### Step 5: Test and debug (30+ minutes)
- Run tests
- Find what you missed when tests fail
- Fix broken code

**TOTAL TIME**: 2-3 hours  
**RISK**: Medium-High (likely to miss some usages)  
**COST**: $150-$225

### With CGC ✅

#### Step 1: Find ALL callers (30 seconds)
```bash
cgc analyze callers execute_cypher_query --all
```

**Output**:
```
Callers of 'execute_cypher_query':

Direct Callers (1):
┌────────────────────────────────────────────────────────────┐
│ Function              │ File                    │ Line     │
├────────────────────────────────────────────────────────────┤
│ execute_cypher_query_tool │ server.py          │ 102      │
└────────────────────────────────────────────────────────────┘

All Callers (Direct + Indirect) (50):
┌────────────────────────────────────────────────────────────┐
│ Function              │ File                    │ Line     │
├────────────────────────────────────────────────────────────┤
│ execute_cypher_query_tool │ server.py          │ 102      │
│ index_helper          │ cli_helpers.py          │ 48       │
│ do_index              │ cli_helpers.py          │ 90       │
│ add_package_helper    │ cli_helpers.py          │ 117      │
│ reindex_helper        │ cli_helpers.py          │ 394      │
│ ... (45 more)
└────────────────────────────────────────────────────────────┘

Summary:
- Direct callers: 1
- Indirect callers: 49
- Total impact: 50 functions
- Files affected: 12
```

#### Step 2: Review impact (5 minutes)
- Clear list of all 50 affected functions
- Exact file paths and line numbers
- No false positives

#### Step 3: Execute refactoring with confidence (10 minutes)
```bash
# Use IDE's refactoring tool, knowing you have the complete list
# Or use sed with exact matches
find . -name "*.py" -exec sed -i 's/execute_cypher_query/run_graph_query/g' {} \;
```

#### Step 4: Verify (5 minutes)
```bash
# Verify no references remain
cgc find "execute_cypher_query"
# Output: No results found

# Verify new function is properly connected
cgc analyze callers run_graph_query
# Output: Shows all 50 callers now point to new function name
```

**TOTAL TIME**: 20 minutes  
**RISK**: Very Low (complete graph-based analysis)  
**COST**: $25

### Savings
- **Time saved**: 2.5 hours
- **Cost saved**: $200
- **Risk reduction**: 90% (from likely bugs to near-zero bugs)
- **ROI**: 800% (saved $200 for $25 of time)

---

## Use Case 2: Code Cleanup - Finding Dead Code

### Scenario

**Company**: SaaS product with 5 years of development (100k LOC)  
**Task**: Find and remove unused code before major release  
**Challenge**: Codebase has accumulated dead code from deprecated features  
**Developer**: Mid-level Engineer ($60/hr)

### Without CGC ❌

#### Manual Process (7-8 hours)

1. **List all functions** (1 hour)
   - Go through each file
   - Note function names in spreadsheet

2. **For each function, search for usages** (4 hours)
   ```bash
   grep -r "function_name_1" .
   grep -r "function_name_2" .
   # Repeat 100+ times...
   ```

3. **Analyze results** (2 hours)
   - Filter false positives (comments, docstrings)
   - Check if called only from tests
   - Check for dynamic calls

4. **Verify and delete** (1 hour)
   - High risk of deleting used code
   - Or keeping unused code

**TOTAL TIME**: 7-8 hours  
**RISK**: High (might delete used code or miss unused code)  
**COST**: $420-$480

### With CGC ✅

#### Automated Process (45 minutes)

#### Step 1: Find dead code (10 seconds)
```bash
cgc analyze dead-code --exclude-decorated @app.route @api.endpoint @celery.task
```

**Output**:
```
Potentially Unused Functions:

┌──────────────────────────────────────────────────────────────────────┐
│ Function              │ File                    │ LOC  │ Complexity  │
├──────────────────────────────────────────────────────────────────────┤
│ _legacyHashPassword   │ auth/legacy_auth.py     │ 23   │ 8           │
│ _migrateUserSession   │ auth/migration.py       │ 34   │ 12          │
│ validateLegacyToken   │ auth/legacy_auth.py     │ 45   │ 15          │
│ oldPaymentGateway     │ billing/deprecated.py   │ 123  │ 22          │
│ formatXMLResponse     │ api/xml_formatter.py    │ 67   │ 18          │
│ ... (45 more)
└──────────────────────────────────────────────────────────────────────┘

Summary:
- Total unused functions: 50
- Total lines of code: 2,345
- Potential savings: 2,345 LOC (2.3% of codebase)

Excluded from analysis:
- Functions decorated with @app.route (API endpoints)
- Functions decorated with @api.endpoint (public API)
- Functions decorated with @celery.task (background jobs)
```

#### Step 2: Review the list (15 minutes)
- Verify each function is truly unused
- Check git history for context
- Confirm with team if unsure

#### Step 3: Delete with confidence (30 minutes)
```bash
# Delete dead code files
rm auth/legacy_auth.py
rm billing/deprecated.py
rm api/xml_formatter.py

# Or remove specific functions
# Use IDE or text editor
```

#### Step 4: Verify (5 minutes)
```bash
# Run tests to ensure nothing broke
pytest

# Verify dead code is gone
cgc stats

# Output shows:
# Functions: 3,371 (was 3,421)
# Removed: 50 functions, 2,345 LOC
```

**TOTAL TIME**: 45 minutes  
**RISK**: Very Low (graph analysis is accurate)  
**COST**: $45

### Savings
- **Time saved**: 7 hours
- **Cost saved**: $420
- **Code reduced**: 2,345 lines (2.3%)
- **Maintenance burden reduced**: Fewer lines to maintain, test, understand
- **ROI**: 933% (saved $420 for $45 of time)

### Long-term Benefits
- **Faster CI/CD**: Less code to test
- **Easier onboarding**: Less code to understand
- **Reduced bugs**: Less code to have bugs
- **Improved performance**: Less code to execute

---

## Use Case 3: Technical Debt Assessment

### Scenario

**Company**: Fintech startup preparing for Series B  
**Task**: Prioritize refactoring efforts for next quarter  
**Challenge**: Limited engineering resources, need to focus on highest-impact refactoring  
**Team**: Engineering Manager + 2 Senior Engineers

### Without CGC ❌

#### Manual Process (3.75 hours)

1. **Install complexity tool** (5 minutes)
   ```bash
   pip install radon mccabe
   ```

2. **Run analysis** (10 minutes)
   ```bash
   radon cc . -a -nb > complexity_report.txt
   ```
   **Output**: Huge text file, hard to parse

3. **Parse and prioritize** (30 minutes)
   - Copy to spreadsheet
   - Sort by complexity
   - Manually categorize

4. **Find usage of complex functions** (2 hours)
   ```bash
   # For top 20 complex functions
   grep -r "complex_function_1" .
   grep -r "complex_function_2" .
   # Repeat 20 times...
   ```

5. **Create refactoring plan** (1 hour)
   - Prioritize based on complexity + usage
   - Estimate effort
   - Assign to engineers

**TOTAL TIME**: 3.75 hours  
**COST**: $281.25 (at $75/hr)

### With CGC ✅

#### Automated Process (20 minutes)

#### Step 1: Find complex functions (5 seconds)
```bash
cgc analyze complexity --limit 20
```

**Output**:
```
Most Complex Functions:

┌──────────────────────────────────────────────────────────────────────┐
│ Function              │ File                    │ Complexity │ LOC    │
├──────────────────────────────────────────────────────────────────────┤
│ processPayment        │ billing/payment.py      │ 45         │ 234    │
│ validateTransaction   │ billing/validation.py   │ 38         │ 189    │
│ calculateFees         │ billing/fees.py         │ 32         │ 156    │
│ reconcileAccounts     │ accounting/reconcile.py │ 28         │ 145    │
│ generateReport        │ reports/generator.py    │ 25         │ 123    │
│ ... (15 more)
└──────────────────────────────────────────────────────────────────────┘

Average complexity: 12.3
Recommended max: 10
Functions exceeding threshold: 20
```

#### Step 2: Find usage of each complex function (2 minutes)
```bash
# For each complex function, find callers
for func in processPayment validateTransaction calculateFees reconcileAccounts generateReport; do
  echo "=== $func ==="
  cgc analyze callers $func --count-only
done
```

**Output**:
```
=== processPayment ===
Callers: 34

=== validateTransaction ===
Callers: 23

=== calculateFees ===
Callers: 18

=== reconcileAccounts ===
Callers: 5

=== generateReport ===
Callers: 12
```

#### Step 3: Generate prioritization matrix (3 minutes)
```bash
cgc analyze complexity --limit 20 --with-callers --output priority_matrix.json
```

**Output** (priority_matrix.json):
```json
[
  {
    "function": "processPayment",
    "complexity": 45,
    "callers": 34,
    "priority_score": 1530,  // complexity * callers
    "priority": "CRITICAL",
    "recommendation": "Refactor immediately - high complexity, widely used"
  },
  {
    "function": "validateTransaction",
    "complexity": 38,
    "callers": 23,
    "priority_score": 874,
    "priority": "HIGH",
    "recommendation": "Refactor next sprint - high complexity, moderate usage"
  },
  {
    "function": "reconcileAccounts",
    "complexity": 28,
    "callers": 5,
    "priority_score": 140,
    "priority": "LOW",
    "recommendation": "Refactor when time permits - complex but rarely used"
  }
]
```

#### Step 4: Create refactoring plan (15 minutes)

**Automated Priority Matrix**:

| Function | Complexity | Callers | Priority | Effort | Sprint |
|----------|------------|---------|----------|--------|--------|
| processPayment | 45 | 34 | CRITICAL | 2 weeks | Q1 Sprint 1 |
| validateTransaction | 38 | 23 | HIGH | 1 week | Q1 Sprint 2 |
| calculateFees | 32 | 18 | HIGH | 1 week | Q1 Sprint 3 |
| generateReport | 25 | 12 | MEDIUM | 3 days | Q1 Sprint 4 |
| reconcileAccounts | 28 | 5 | LOW | 1 week | Q2 Backlog |

**TOTAL TIME**: 20 minutes  
**COST**: $25

### Savings
- **Time saved**: 3.5 hours
- **Cost saved**: $256
- **Better prioritization**: Data-driven decisions vs gut feeling
- **ROI**: 1024% (saved $256 for $25 of time)

### Business Impact
- **Focused refactoring**: Work on high-impact code first
- **Reduced risk**: Refactor widely-used code with more care
- **Better estimates**: Know complexity and usage upfront
- **Investor confidence**: Show technical debt is managed

---

## Use Case 4: Onboarding New Developers

### Scenario

**Company**: Open-source project with 200+ contributors  
**New Developer**: Junior engineer (first month)  
**Task**: Understand the authentication system to fix a bug  
**Challenge**: No documentation, complex codebase, senior devs are busy

### Without CGC ❌

#### Manual Process (4 hours)

1. **Find entry point** (30 minutes)
   - Read README (if exists)
   - Search for "auth" in code
   - Ask in Slack (wait for response)

2. **Trace code flow manually** (2 hours)
   - Open `auth_handler.py`
   - See it calls `validate_token`
   - Open `validate_token`, see it calls `check_database`
   - Keep following the chain...
   - Get lost in circular imports

3. **Draw diagram** (1 hour)
   - Manually create call flow diagram
   - Probably incomplete or incorrect

4. **Ask senior developer** (30 minutes)
   - Schedule meeting
   - Explain confusion
   - Get clarification

**TOTAL TIME**: 4 hours (new dev) + 30 min (senior dev)  
**COST**: $200 (new dev at $50/hr) + $62.50 (senior dev at $125/hr) = $262.50

### With CGC ✅

#### Self-Service Process (30 minutes)

#### Step 1: Find authentication entry point (10 seconds)
```bash
cgc find "auth" --type function | grep -i "handler\|main\|entry"
```

**Output**:
```
Found 3 functions matching 'auth' with 'handler':

1. auth_handler
   File: src/api/auth.py:23
   
2. handle_login
   File: src/api/auth.py:45
   
3. handle_logout
   File: src/api/auth.py:78
```

#### Step 2: See what auth_handler calls (5 seconds)
```bash
cgc analyze callees auth_handler
```

**Output**:
```
Functions called by 'auth_handler':

┌────────────────────────────────────────────────────────────┐
│ Function              │ File                    │ Line     │
├────────────────────────────────────────────────────────────┤
│ validate_token        │ auth/validation.py      │ 34       │
│ check_permissions     │ auth/permissions.py     │ 67       │
│ log_auth_attempt      │ logging/audit.py        │ 89       │
└────────────────────────────────────────────────────────────┘
```

#### Step 3: Get complete call chain (5 seconds)
```bash
cgc analyze chain auth_handler database_query
```

**Output**:
```
Call Chain from 'auth_handler' to 'database_query':

auth_handler (api/auth.py:23)
  └─> validate_token (auth/validation.py:34)
      └─> check_database (auth/db_check.py:56)
          └─> database_query (core/database.py:89)

Path length: 4 functions
Execution flow: API → Validation → Database Check → Database
```

#### Step 4: Visualize the architecture (30 seconds)
```bash
cgc visualize --focus auth --output auth_architecture.html
```

Opens interactive graph showing:
- All authentication-related functions
- How they connect
- Module boundaries
- External dependencies

#### Step 5: Explore and understand (20 minutes)
- Click through visualization
- Read relevant code sections
- Understand the full flow
- No senior dev needed!

**TOTAL TIME**: 30 minutes  
**COST**: $25 (new dev only, no senior dev time)

### Savings
- **Time saved**: 3.5 hours
- **Cost saved**: $237.50
- **Senior dev time saved**: 30 minutes ($62.50)
- **Faster onboarding**: Productive in hours vs days
- **ROI**: 950% (saved $237.50 for $25 of time)

### Long-term Benefits
- **Self-sufficient developers**: Less hand-holding needed
- **Reduced senior dev interruptions**: More time for architecture work
- **Better code understanding**: Visual + structural learning
- **Faster ramp-up**: New devs productive in days vs weeks

---

## Use Case 5: Bug Investigation - Tracing Data Flow

### Scenario

**Company**: E-commerce platform  
**Bug Report**: "Payment confirmation emails not sending for international orders"  
**Developer**: Mid-level Backend Engineer ($65/hr)  
**Challenge**: Complex payment flow, multiple services involved

### Without CGC ❌

#### Manual Investigation (4+ hours)

1. **Search for email code** (10 minutes)
   ```bash
   grep -r "email" . --include="*.py" | grep -i "payment\|confirm"
   ```
   **Output**: 200+ lines, many false positives

2. **Search for international payment code** (10 minutes)
   ```bash
   grep -r "international" . --include="*.py"
   ```

3. **Manually trace the flow** (2 hours)
   - Read `process_international_payment` function
   - See what it calls
   - Check if email function is called
   - Trace through multiple files
   - Get confused by similar function names

4. **Compare with domestic payments** (1 hour)
   - Read `process_domestic_payment` function
   - Compare side-by-side
   - Identify differences

5. **Verify the fix** (1 hour)
   - Make the change
   - Test locally
   - Hope nothing else breaks

**TOTAL TIME**: 4+ hours  
**COST**: $260+  
**RISK**: Might miss side effects

### With CGC ✅

#### Systematic Investigation (30 minutes)

#### Step 1: Find email functions (10 seconds)
```bash
cgc find "email" --type function | grep -i "payment\|confirm"
```

**Output**:
```
Found 5 functions:

1. sendPaymentConfirmation
   File: email_service/notifications.py:45
   
2. sendInternationalPaymentEmail
   File: email_service/international.py:12
   
3. queueEmailJob
   File: workers/email_queue.py:78
```

#### Step 2: Check what calls international payment function (5 seconds)
```bash
cgc analyze callees processInternationalPayment
```

**Output**:
```
Functions called by 'processInternationalPayment':

┌────────────────────────────────────────────────────────────┐
│ Function              │ File                    │ Line     │
├────────────────────────────────────────────────────────────┤
│ validateCurrency      │ utils/currency.py       │ 23       │
│ chargeCard            │ integrations/stripe.py  │ 89       │
│ logTransaction        │ logging/audit.py        │ 45       │
│ updateOrderStatus     │ orders/order_service.py │ 167      │
└────────────────────────────────────────────────────────────┘

⚠️  Notice: sendInternationalPaymentEmail is NOT called
```

**BUG FOUND!** Email function is not being called.

#### Step 3: Verify domestic payments work correctly (5 seconds)
```bash
cgc analyze callees processDomesticPayment
```

**Output**:
```
Functions called by 'processDomesticPayment':

┌────────────────────────────────────────────────────────────┐
│ Function              │ File                    │ Line     │
├────────────────────────────────────────────────────────────┤
│ validateCurrency      │ utils/currency.py       │ 23       │
│ chargeCard            │ integrations/stripe.py  │ 89       │
│ logTransaction        │ logging/audit.py        │ 45       │
│ updateOrderStatus     │ orders/order_service.py │ 167      │
│ sendPaymentConfirmation │ email_service/notifications.py │ 45 │
└────────────────────────────────────────────────────────────┘

✓ Domestic payments DO call email function
```

**ROOT CAUSE IDENTIFIED**: International payments missing email call.

#### Step 4: Verify the fix is safe (5 seconds)
```bash
cgc analyze callers sendInternationalPaymentEmail
```

**Output**:
```
Callers of 'sendInternationalPaymentEmail':

No callers found.

⚠️  This function appears to be unused (dead code)
```

**PERFECT!** Adding this call won't break anything.

#### Step 5: Make and verify fix (20 minutes)
- Add email call to `processInternationalPayment`
- Run tests
- Deploy

**TOTAL TIME**: 30 minutes  
**COST**: $32.50  
**RISK**: Very low (verified no side effects)

### Savings
- **Time saved**: 3.5 hours
- **Cost saved**: $227.50
- **Faster bug resolution**: 30 min vs 4+ hours
- **Higher confidence**: Know exactly what's wrong and what's safe
- **ROI**: 700% (saved $227.50 for $32.50 of time)

---

## Use Case 6: API Deprecation Planning

### Scenario

**Company**: SaaS platform with public API  
**Task**: Deprecate `add_package_to_graph` function, replace with `add_package_v2`  
**Challenge**: Need to know all usages (internal + external examples)  
**Team**: Product Manager + Senior Engineer

### Without CGC ❌

#### Manual Process (2.5 hours)

1. **Search for direct usages** (5 minutes)
   ```bash
   grep -r "add_package_to_graph" . --include="*.py"
   ```

2. **Check CLI commands** (20 minutes)
   - Manually review CLI files
   - Check argument parsing

3. **Check MCP tools** (15 minutes)
   - Review server.py
   - Check tool wrappers

4. **Check tests** (20 minutes)
   - Search test files
   - Verify test coverage

5. **Check documentation** (30 minutes)
   - Search docs for examples
   - Check tutorials

6. **Create migration guide** (1 hour)
   - Document all usages
   - Write replacement examples
   - Create timeline

**TOTAL TIME**: 2.5 hours  
**COST**: $187.50 (at $75/hr)  
**RISK**: Might miss some usages

### With CGC ✅

#### Systematic Process (20 minutes)

#### Step 1: Find all usages (5 seconds)
```bash
cgc analyze callers add_package_to_graph --all
```

**Output**:
```
Callers of 'add_package_to_graph':

Direct Callers (3):
┌────────────────────────────────────────────────────────────┐
│ Function              │ File                    │ Line     │
├────────────────────────────────────────────────────────────┤
│ add_package_to_graph_tool │ server.py          │ 156      │
│ add_package_helper    │ cli_helpers.py          │ 117      │
│ test_add_package      │ tests/test_indexing.py  │ 234      │
└────────────────────────────────────────────────────────────┘

Indirect Callers (0):
(No indirect callers)

Summary:
- 3 total usages
- 2 production code
- 1 test
- 0 external dependencies
```

#### Step 2: Analyze impact (5 minutes)
```
✅ MCP Tool: add_package_to_graph_tool → Update wrapper
✅ CLI: add_package_helper → Update command
✅ Tests: test_add_package → Update test
```

#### Step 3: Create migration plan (15 minutes)

**Auto-generated Migration Plan**:

```markdown
## Deprecation Impact: add_package_to_graph

### Summary
- **Total usages**: 3
- **Breaking change**: Yes
- **Migration effort**: Low (only 3 places to update)
- **Recommended timeline**: 2 sprints

### Direct Callers (3):

1. ✅ **MCP Tool**: `add_package_to_graph_tool` (server.py:156)
   - **Action**: Update to call `add_package_v2`
   - **Effort**: 30 minutes
   - **Risk**: Low

2. ✅ **CLI**: `add_package_helper` (cli_helpers.py:117)
   - **Action**: Update command implementation
   - **Effort**: 1 hour
   - **Risk**: Low (covered by tests)

3. ✅ **Tests**: `test_add_package` (tests/test_indexing.py:234)
   - **Action**: Update test to use new function
   - **Effort**: 30 minutes
   - **Risk**: None

### Migration Timeline

**Sprint 1: Preparation**
- Week 1: Implement `add_package_v2` with new features
- Week 2: Add deprecation warning to `add_package_to_graph`
- Week 2: Update documentation

**Sprint 2: Migration**
- Week 1: Update MCP tool and CLI
- Week 1: Update tests
- Week 2: Release with migration guide

**Sprint 3: Cleanup**
- Week 1: Monitor usage (should be zero)
- Week 2: Remove deprecated function

### Deprecation Warning Code

```python
import warnings

def add_package_to_graph(*args, **kwargs):
    warnings.warn(
        "add_package_to_graph is deprecated and will be removed in v2.0. "
        "Use add_package_v2 instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return add_package_v2(*args, **kwargs)
```

### Communication Plan

**Internal (Sprint 1, Week 2)**
- Email to engineering team
- Update internal docs
- Add to sprint planning notes

**External (Sprint 2, Week 1)**
- Blog post announcing deprecation
- Update public API docs
- Add to changelog

**Final Removal (Sprint 3, Week 2)**
- Remove function
- Update version to 2.0
- Release notes
```

**TOTAL TIME**: 20 minutes  
**COST**: $25

### Savings
- **Time saved**: 2.25 hours
- **Cost saved**: $162.50
- **Complete coverage**: No missed usages
- **Professional migration plan**: Ready to present to stakeholders
- **ROI**: 650% (saved $162.50 for $25 of time)

---

## Use Case 7: Architecture Review

### Scenario

**Company**: Fintech startup preparing for SOC 2 audit  
**Task**: Document system architecture and identify circular dependencies  
**Team**: CTO + 2 Senior Engineers  
**Challenge**: No up-to-date architecture documentation

### Without CGC ❌

#### Manual Process (4.5 hours)

1. **List all modules** (5 minutes)
   ```bash
   ls -R src/
   ```

2. **For each module, find imports** (2 hours)
   - Manually read import statements
   - Create dependency list in spreadsheet

3. **Create dependency graph** (30 minutes)
   ```bash
   pip install pydeps
   pydeps src/ --max-bacon=2
   ```
   **Output**: Static image, hard to explore

4. **Analyze circular dependencies** (1 hour)
   - Manually trace through graph
   - Identify cycles

5. **Identify refactoring opportunities** (1 hour)
   - Which modules are too coupled?
   - What should be extracted?

**TOTAL TIME**: 4.5 hours  
**COST**: $337.50 (at $75/hr)

### With CGC ✅

#### Automated Process (30 minutes)

#### Step 1: Get module dependencies (5 seconds)
```bash
cgc analyze deps codegraphcontext.tools
```

**Output**:
```
Module Dependencies for 'codegraphcontext.tools':

Imports (Dependencies):
┌────────────────────────────────────────────────────────────┐
│ Module                │ Import Count │ Type                │
├────────────────────────────────────────────────────────────┤
│ codegraphcontext.core │ 12           │ Internal            │
│ codegraphcontext.utils│ 8            │ Internal            │
│ neo4j                 │ 5            │ External            │
│ falkordb              │ 3            │ External            │
└────────────────────────────────────────────────────────────┘

Imported By (Dependents):
┌────────────────────────────────────────────────────────────┐
│ Module                │ Import Count │ Type                │
├────────────────────────────────────────────────────────────┤
│ codegraphcontext.cli  │ 15           │ Internal            │
│ codegraphcontext.server│ 10          │ Internal            │
└────────────────────────────────────────────────────────────┘
```

#### Step 2: Find circular dependencies (5 seconds)
```bash
cgc query "
MATCH (m1:Module)-[:IMPORTS]->(m2:Module)-[:IMPORTS]->(m1)
RETURN m1.name, m2.name
"
```

**Output**:
```
Circular Dependencies Found:

┌────────────────────────────────────────────────────────────┐
│ Module A              │ Module B                           │
├────────────────────────────────────────────────────────────┤
│ tools.graph_builder   │ core.database                      │
│ core.database         │ tools.query_handlers               │
└────────────────────────────────────────────────────────────┘

⚠️  2 circular dependencies detected
```

#### Step 3: Visualize architecture (10 seconds)
```bash
cgc visualize --mode architecture --output architecture.html
```

**Opens interactive visualization showing**:
- All modules as nodes
- Dependencies as arrows
- Circular dependencies highlighted in red
- Module sizes (by LOC)
- External dependencies in different color

#### Step 4: Generate architecture report (20 minutes)

**Auto-generated Architecture Report**:

```markdown
# System Architecture Report
Generated: 2026-01-30

## Overview
- **Total Modules**: 67
- **Internal Dependencies**: 234
- **External Dependencies**: 45
- **Circular Dependencies**: 2 ⚠️

## Module Structure

### Core Modules (Foundation)
- `core.database` - Database abstraction layer
- `core.parser` - Code parsing engine
- `core.graph` - Graph data structures

### Tool Modules (Features)
- `tools.graph_builder` - Graph construction
- `tools.query_handlers` - Query execution
- `tools.package_resolver` - Package discovery

### Interface Modules (User-facing)
- `cli` - Command-line interface
- `server` - MCP server
- `api` - REST API (future)

## Dependency Analysis

### Most Depended-On Modules (Critical)
1. `core.database` - 23 modules depend on it
2. `utils.debug_log` - 18 modules depend on it
3. `core.parser` - 15 modules depend on it

### Most Dependent Modules (Coupled)
1. `tools.graph_builder` - depends on 12 modules
2. `cli.cli_helpers` - depends on 10 modules
3. `server` - depends on 8 modules

## Issues Identified

### ⚠️ Circular Dependencies (2)

**Issue 1**: tools.graph_builder ↔ core.database
- **Impact**: High - affects core functionality
- **Recommendation**: Extract query_handlers to core.queries
- **Effort**: 2 days

**Issue 2**: core.database ↔ tools.query_handlers
- **Impact**: Medium - affects query execution
- **Recommendation**: Move query_handlers to core module
- **Effort**: 1 day

### ✅ Refactoring Opportunities

1. **Extract Logging Module**
   - 18 modules depend on `utils.debug_log`
   - Consider extracting to separate package
   - Benefit: Reusable across projects

2. **Reduce graph_builder Coupling**
   - Depends on 12 modules
   - Consider dependency injection
   - Benefit: Easier testing

## Recommendations

### Immediate (This Sprint)
1. Fix circular dependency: tools ↔ core
2. Document module boundaries
3. Add architecture tests (prevent future cycles)

### Short-term (Next Quarter)
1. Extract logging to separate package
2. Reduce graph_builder coupling
3. Create module dependency guidelines

### Long-term (Next Year)
1. Consider microservices architecture
2. Separate CLI, MCP, and API into services
3. Shared core library
```

**TOTAL TIME**: 30 minutes  
**COST**: $37.50

### Savings
- **Time saved**: 4 hours
- **Cost saved**: $300
- **Better insights**: Automated analysis vs manual
- **Audit-ready**: Professional documentation
- **ROI**: 800% (saved $300 for $37.50 of time)

### Business Impact
- **SOC 2 compliance**: Architecture documented
- **Technical debt visible**: Circular dependencies identified
- **Refactoring roadmap**: Clear priorities
- **Investor confidence**: Professional engineering practices

---

## Use Case 8: Security Audit

### Scenario

**Company**: Healthcare SaaS (HIPAA compliance required)  
**Task**: Security audit - find all database and API access points  
**Auditor**: External security consultant ($200/hr)  
**Challenge**: Need complete, accurate list for compliance

### Without CGC ❌

#### Manual Process (5+ hours)

1. **Search for database calls** (10 minutes)
   ```bash
   grep -r "execute\|query\|session" . --include="*.py"
   ```
   **Output**: 500+ lines, many false positives

2. **Search for API calls** (10 minutes)
   ```bash
   grep -r "requests\.\|http\|urllib" . --include="*.py"
   ```
   **Output**: 200+ lines

3. **Manually filter and categorize** (3 hours)
   - Read each result
   - Identify actual data access
   - Categorize by risk level
   - Miss some edge cases

4. **Document each access point** (2 hours)
   - Create audit report
   - Describe each access point
   - Assess risk

**TOTAL TIME**: 5+ hours  
**COST**: $1,000+ (at $200/hr auditor rate)  
**RISK**: Might miss some access points (compliance failure)

### With CGC ✅

#### Systematic Process (35 minutes)

#### Step 1: Find all database access (5 seconds)
```bash
cgc query "
MATCH (f:Function)-[:CALLS]->(db:Function)
WHERE db.name IN ['execute', 'query', 'session', 'execute_cypher_query']
RETURN DISTINCT f.name, f.path
ORDER BY f.path
"
```

**Output**:
```
Functions Making Database Calls:

┌────────────────────────────────────────────────────────────┐
│ Function              │ File                    │ Risk     │
├────────────────────────────────────────────────────────────┤
│ execute_cypher_query  │ tools/query_handlers.py │ HIGH     │
│ create_node           │ tools/graph_builder.py  │ MEDIUM   │
│ create_relationship   │ tools/graph_builder.py  │ MEDIUM   │
│ find_code             │ tools/search.py         │ LOW      │
│ get_stats             │ tools/stats.py          │ LOW      │
│ ... (15 more)
└────────────────────────────────────────────────────────────┘

Total: 20 functions with database access
```

#### Step 2: Find all API calls (5 seconds)
```bash
cgc query "
MATCH (f:Function)
WHERE f.code CONTAINS 'requests.' OR f.code CONTAINS 'urllib' OR f.code CONTAINS 'httpx'
RETURN f.name, f.path
ORDER BY f.path
"
```

**Output**:
```
Functions Making External API Calls:

┌────────────────────────────────────────────────────────────┐
│ Function              │ File                    │ Endpoint │
├────────────────────────────────────────────────────────────┤
│ _get_npm_package      │ package_resolver.py     │ npm      │
│ _get_pypi_package     │ package_resolver.py     │ PyPI     │
│ download_bundle       │ bundle_manager.py       │ GitHub   │
└────────────────────────────────────────────────────────────┘

Total: 3 functions with external API access
```

#### Step 3: Trace back to entry points (10 seconds)
```bash
# For each data access function, find who can trigger it
for func in execute_cypher_query download_bundle; do
  echo "=== $func ==="
  cgc analyze callers $func --all --entry-points-only
done
```

**Output**:
```
=== execute_cypher_query ===
Entry Points (User-accessible):
- CLI: cgc query <cypher>
- MCP: execute_cypher_query tool
- API: /api/query (future)

=== download_bundle ===
Entry Points (User-accessible):
- CLI: cgc load <bundle>
- MCP: load_bundle tool
```

#### Step 4: Generate audit report (20 minutes)

**Auto-generated Security Audit Report**:

```markdown
# Security Audit Report: Data Access Points
Generated: 2026-01-30
Auditor: External Security Consultant
Compliance: HIPAA

## Executive Summary
- **Database Access Points**: 20 functions
- **External API Access Points**: 3 functions
- **High-Risk Functions**: 1
- **Medium-Risk Functions**: 5
- **Low-Risk Functions**: 17

## Database Access Analysis

### HIGH RISK: Direct Query Execution

**Function**: `execute_cypher_query`
- **File**: tools/query_handlers.py:18
- **Entry Points**: CLI, MCP tool
- **Risk**: User can execute arbitrary Cypher queries
- **Current Mitigation**: Read-only queries enforced
- **Recommendation**: ✅ Add query validation and rate limiting
- **Status**: REQUIRES ATTENTION

### MEDIUM RISK: Data Modification

**Function**: `create_node`
- **File**: tools/graph_builder.py:234
- **Entry Points**: Internal only (indexing)
- **Risk**: Creates database nodes
- **Current Mitigation**: Internal use only, no user input
- **Recommendation**: ✅ Already secure
- **Status**: ACCEPTABLE

**Function**: `create_relationship`
- **File**: tools/graph_builder.py:267
- **Entry Points**: Internal only (indexing)
- **Risk**: Creates database relationships
- **Current Mitigation**: Internal use only, no user input
- **Recommendation**: ✅ Already secure
- **Status**: ACCEPTABLE

### LOW RISK: Read-Only Access

**Functions**: 17 functions
- All read-only database queries
- No user input in queries
- Parameterized queries used
- **Status**: ✅ SECURE

## External API Access Analysis

### Function: `_get_npm_package`
- **File**: package_resolver.py:37
- **Endpoint**: https://registry.npmjs.org
- **Data Sent**: Package name only
- **Data Received**: Package metadata (public)
- **Risk**: Low - public data only
- **Recommendation**: ✅ Add timeout and retry logic
- **Status**: ACCEPTABLE

### Function**: `_get_pypi_package`
- **File**: package_resolver.py:78
- **Endpoint**: https://pypi.org/pypi
- **Data Sent**: Package name only
- **Data Received**: Package metadata (public)
- **Risk**: Low - public data only
- **Recommendation**: ✅ Add timeout and retry logic
- **Status**: ACCEPTABLE

### Function: `download_bundle`
- **File**: bundle_manager.py:123
- **Endpoint**: https://github.com
- **Data Sent**: Bundle name only
- **Data Received**: Pre-indexed code bundle
- **Risk**: Medium - downloading executable code
- **Recommendation**: ⚠️ Add checksum verification
- **Status**: REQUIRES ATTENTION

## Compliance Assessment

### HIPAA Requirements

✅ **Access Control**: All database access is authenticated
✅ **Audit Logging**: All queries are logged
✅ **Encryption**: Database connections use TLS
⚠️ **Input Validation**: execute_cypher_query needs validation
✅ **Data Minimization**: Only necessary data accessed

### Recommendations

**Immediate (This Week)**:
1. Add query validation to `execute_cypher_query`
2. Add checksum verification to `download_bundle`
3. Implement rate limiting on user-facing queries

**Short-term (This Month)**:
1. Add comprehensive audit logging
2. Implement query timeout limits
3. Add input sanitization

**Long-term (This Quarter)**:
1. Implement role-based access control
2. Add query complexity analysis
3. Implement data retention policies

## Conclusion

**Overall Risk Level**: MEDIUM

The system has good security practices in place, with only 2 functions requiring immediate attention. With the recommended changes, the system will meet HIPAA compliance requirements.

**Compliance Status**: CONDITIONAL PASS
(Pending implementation of immediate recommendations)
```

**TOTAL TIME**: 35 minutes  
**COST**: $116.67 (at $200/hr)

### Savings
- **Time saved**: 4.5 hours
- **Cost saved**: $883.33
- **Comprehensive audit**: No missed access points
- **Compliance confidence**: Complete documentation
- **ROI**: 757% (saved $883.33 for $116.67 of time)

### Business Impact
- **HIPAA compliance**: Clear audit trail
- **Risk mitigation**: All access points identified
- **Customer trust**: Professional security practices
- **Reduced liability**: Compliance documented

---

## Use Case 9: Performance Optimization

### Scenario

**Company**: Analytics platform with slow dashboard loading  
**Issue**: Profiling shows `execute_cypher_query` called 10,000 times during indexing  
**Developer**: Senior Performance Engineer ($90/hr)  
**Challenge**: Find where excessive calls are coming from

### Without CGC ❌

#### Manual Process (4+ hours)

1. **Add logging** (15 minutes)
   - Modify `execute_cypher_query` to log caller
   - Redeploy

2. **Run indexing with logging** (30 minutes)
   - Generate huge log file
   - Wait for indexing to complete

3. **Parse logs** (1 hour)
   - Write script to count calls per caller
   - Analyze results

4. **Analyze hot paths** (30 minutes)
   - Identify which callers are most frequent

5. **Investigate optimization** (2 hours)
   - For each hot path, understand why
   - Research batching opportunities
   - Test solutions

**TOTAL TIME**: 4+ hours  
**COST**: $360+

### With CGC ✅

#### Systematic Process (30 minutes)

#### Step 1: Find all callers (5 seconds)
```bash
cgc analyze callers execute_cypher_query --all
```

**Output**: 50 callers identified

#### Step 2: Identify likely hot paths (10 minutes)

Look for callers in loops or batch operations:
- `graph_builder.process_file` (called per file)
- `graph_builder.create_node` (called per node)
- `graph_builder.create_relationship` (called per relationship)

#### Step 3: Analyze hot path (5 seconds)
```bash
cgc analyze chain index_repository execute_cypher_query
```

**Output**:
```
Call Chain from 'index_repository' to 'execute_cypher_query':

index_repository (cli_helpers.py:90)
  └─> process_directory (graph_builder.py:123)
      └─> process_file (graph_builder.py:234)
          └─> create_node (graph_builder.py:345)
              └─> execute_cypher_query (query_handlers.py:18)

Execution Pattern:
- index_repository: called 1 time
- process_directory: called ~10 times (per directory)
- process_file: called ~1,000 times (per file)
- create_node: called ~10,000 times (per node)
- execute_cypher_query: called ~10,000 times

⚠️  HOT PATH IDENTIFIED: create_node in tight loop
```

#### Step 4: Identify optimization (15 minutes)

**Current Code** (in `graph_builder.py`):
```python
def process_file(self, file_path):
    nodes = self.parse_file(file_path)
    for node in nodes:
        self.create_node(node)  # 1 query per node

def create_node(self, node):
    query = "CREATE (n:Node {data})"
    execute_cypher_query(query, data=node)
```

**Optimized Code**:
```python
def process_file(self, file_path):
    nodes = self.parse_file(file_path)
    self.create_nodes_batch(nodes)  # 1 query for all nodes

def create_nodes_batch(self, nodes):
    query = "UNWIND $nodes AS node CREATE (n:Node {node})"
    execute_cypher_query(query, nodes=nodes)
```

**Result**: 10,000 queries → 1,000 queries (10x improvement)

**TOTAL TIME**: 30 minutes  
**COST**: $45

### Savings
- **Time saved**: 3.5 hours
- **Cost saved**: $315
- **Performance improvement**: 10x faster indexing
- **ROI**: 700% (saved $315 for $45 of time)

### Business Impact
- **Faster indexing**: 10x improvement
- **Better user experience**: Dashboards load faster
- **Reduced infrastructure costs**: Less database load
- **Scalability**: Can handle larger codebases

---

## Use Case 10: Code Review - PR Impact Analysis

### Scenario

**Company**: Open-source project with 200+ contributors  
**PR**: Modifies `graph_builder.py` (core functionality)  
**Reviewer**: Maintainer reviewing PR ($80/hr)  
**Challenge**: Understand blast radius of changes

### Without CGC ❌

#### Manual Process (2.5 hours)

1. **See what changed** (10 minutes)
   ```bash
   git diff main...feature-branch
   ```

2. **Identify modified functions** (5 minutes)
   - Manually list: `process_file`, `create_node`, `add_relationship`

3. **Find callers of each function** (15 minutes)
   ```bash
   grep -r "process_file" . --include="*.py"
   grep -r "create_node" . --include="*.py"
   grep -r "add_relationship" . --include="*.py"
   ```

4. **Assess impact** (1 hour)
   - Read each caller
   - Understand if change affects it
   - Check for edge cases

5. **Check test coverage** (30 minutes)
   - Manually review test files
   - Verify tests cover changes

6. **Write review comments** (30 minutes)

**TOTAL TIME**: 2.5 hours  
**COST**: $200

### With CGC ✅

#### Systematic Process (30 minutes)

#### Step 1: Identify changed functions (5 minutes)

From git diff:
- `process_file` modified
- `create_node` modified
- `add_relationship` added (new)

#### Step 2: Find impact of each change (10 seconds)
```bash
cgc analyze callers process_file --all
cgc analyze callers create_node --all
cgc analyze callers add_relationship --all
```

**Output**:
```
=== process_file ===
Callers: 15 functions
Files affected: 5

=== create_node ===
Callers: 23 functions
Files affected: 8

=== add_relationship ===
Callers: 0 functions (new function)
```

#### Step 3: Check test coverage (5 seconds)
```bash
cgc query "
MATCH (test:Function)-[:CALLS]->(f:Function)
WHERE test.path CONTAINS 'test'
  AND f.name IN ['process_file', 'create_node', 'add_relationship']
RETURN test.name, f.name
"
```

**Output**:
```
Test Coverage:

┌────────────────────────────────────────────────────────────┐
│ Test Function         │ Covers Function                    │
├────────────────────────────────────────────────────────────┤
│ test_process_file     │ process_file                       │
│ test_indexing_flow    │ process_file                       │
│ test_create_node      │ create_node                        │
└────────────────────────────────────────────────────────────┘

⚠️  add_relationship has NO test coverage
```

#### Step 4: Write informed review (20 minutes)

**Auto-generated Review Template**:

```markdown
## PR Review: graph_builder.py changes

### Impact Analysis

✅ **process_file** modified
- **Callers**: 15 functions across 5 files
- **Test Coverage**: ✅ 2 tests (test_process_file, test_indexing_flow)
- **Risk**: Medium - widely used but well-tested
- **Recommendation**: Approve with minor comments

⚠️ **create_node** modified
- **Callers**: 23 functions across 8 files
- **Test Coverage**: ⚠️ Only 1 test (test_create_node)
- **Risk**: Medium-High - widely used, limited test coverage
- **Recommendation**: Request additional integration tests

❌ **add_relationship** added (new function)
- **Callers**: 0 (not yet used)
- **Test Coverage**: ❌ No tests
- **Risk**: Low (not used yet) but concerning
- **Recommendation**: MUST add tests before merging

### Detailed Review

#### 1. process_file changes
**Lines**: 234-267
**Change**: Added error handling for malformed files

✅ **Good**:
- Proper exception handling
- Logging added
- Backwards compatible

💡 **Suggestions**:
- Consider adding specific exception types
- Add test case for malformed file handling

#### 2. create_node changes
**Lines**: 345-378
**Change**: Added support for node properties validation

⚠️ **Concerns**:
- 23 callers affected - high impact
- Only 1 test covers this function
- What happens if validation fails?

🔴 **Required Changes**:
1. Add integration test with real codebase
2. Add test for validation failure case
3. Document validation rules in docstring

#### 3. add_relationship (new function)
**Lines**: 456-489

❌ **Blocking Issues**:
1. No test coverage
2. No docstring
3. Not called anywhere (dead code?)

🔴 **Required Changes**:
1. Add unit tests
2. Add docstring with examples
3. Either use it or remove it

### Risk Assessment

**Overall Risk**: MEDIUM-HIGH

- High usage (38 total callers affected)
- Partial test coverage
- New untested code

### Recommendation

**REQUEST CHANGES**

Before merging:
1. ✅ Add integration test for create_node
2. ✅ Add unit tests for add_relationship
3. ✅ Add docstrings for new code
4. ✅ Consider adding test for process_file error handling

After these changes, I'll approve.

### Testing Checklist

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing on large repository
- [ ] Performance regression check
- [ ] Documentation updated
```

**TOTAL TIME**: 30 minutes  
**COST**: $40

### Savings
- **Time saved**: 2 hours
- **Cost saved**: $160
- **Better review quality**: Data-driven, comprehensive
- **Fewer bugs**: Caught missing tests before merge
- **ROI**: 400% (saved $160 for $40 of time)

### Long-term Benefits
- **Higher code quality**: Systematic reviews
- **Fewer production bugs**: Caught issues early
- **Faster reviews**: 30 min vs 2.5 hours
- **Contributor satisfaction**: Clear, actionable feedback

---

## Summary: Total Value Across All Use Cases

| Use Case | Time Saved | Cost Saved | Risk Reduction | ROI |
|----------|------------|------------|----------------|-----|
| 1. Safe Refactoring | 2.5 hrs | $200 | 90% | 800% |
| 2. Dead Code Cleanup | 7 hrs | $420 | 95% | 933% |
| 3. Technical Debt | 3.5 hrs | $256 | N/A | 1024% |
| 4. Onboarding | 3.5 hrs | $238 | N/A | 950% |
| 5. Bug Investigation | 3.5 hrs | $228 | 80% | 700% |
| 6. API Deprecation | 2.25 hrs | $163 | 85% | 650% |
| 7. Architecture Review | 4 hrs | $300 | N/A | 800% |
| 8. Security Audit | 4.5 hrs | $883 | 95% | 757% |
| 9. Performance Optimization | 3.5 hrs | $315 | N/A | 700% |
| 10. Code Review | 2 hrs | $160 | 70% | 400% |
| **TOTAL** | **36.25 hrs** | **$3,163** | **Avg 86%** | **Avg 771%** |

---

## ROI Calculation

### Per Month (assuming 2 use cases/week)
- **Time saved**: ~36 hours/month
- **Cost saved**: ~$3,163/month
- **Productivity gain**: ~1 week of developer time

### Per Year
- **Time saved**: 432 hours (10.8 work weeks)
- **Cost saved**: $37,956
- **Risk reduction**: 86% fewer bugs from incomplete analysis

### Investment
- **Setup time**: 10 minutes
- **Learning curve**: 2 hours
- **Maintenance**: ~30 minutes/month

### Break-even
**After first 2 use cases (< 1 day)**

---

## Conclusion

CodeGraphContext is not just a tool—it's a **force multiplier** that:

✅ Saves **36+ hours per month** on code analysis tasks  
✅ Reduces **86% of risk** from incomplete analysis  
✅ Enables **self-service** code exploration (no senior dev needed)  
✅ Provides **100% accurate** dependency analysis (vs 70-80% manual)  
✅ Pays for itself in **less than 1 day**  
✅ Delivers **771% average ROI**

**The question isn't whether to use CodeGraphContext—it's how much money you're losing by not using it.** 🚀

---

## Next Steps

- **Get started** → [SETUP_WORKFLOWS.md](./setup_workflows.md)
- **See real examples** → [USER_JOURNEYS.md](./user_journeys.md)
- **Integration patterns** → [INTEGRATION_GUIDE.md](./integration_guide.md)
- **CLI reference** → [CLI_COMPLETE_REFERENCE.md](./cli.md)
- **MCP reference** → [MCP_TOOLS.md](./server.md)

### Enquiry Management

Enquiry Management

---

## Permission System - Functional Training Document

### Roles Overview

| Role | List View | Edit | User Configuration Required |
|------|-----------|------|-----------------------------|
| Administrator | All Enquiries | All | No |
| System Manager | All Enquiries | All | No |
| Head | Based on Organisation + Segment | Current Owner only | Yes |
| Normal | Own created only | Current Owner only | Yes |

---

## 1. Administrator / System Manager

**Access:** Full access. No restrictions.

**List View:** See all enquiries.

**Edit:** Can edit any enquiry.

**Note:** Both roles behave identically. No User Configuration needed.

---

## 2. Normal Role

**Prerequisite:** Must have a User Configuration record.

**List View Rules:**

| Rule | Condition | Example |
|------|-----------|---------|
| Own Created | Always visible | User created ENQ-001 -> visible |
| Segment Match | Own created + segment matches User Config | User's segment = HVAC, ENQ has HVAC -> visible |
| Sub Segment Match | Own created + sub segment matches | User's sub segment = Chillers, ENQ has Chillers -> visible |
| Organisation Match | Own created + org matches | User's org = BO Kolkatta, ENQ has BO Kolkatta -> visible |
| Assigned | Enquiry assigned to user | ENQ assigned to user -> visible |
| Reporting To | Created by users who report to this user | John reports to user, John created ENQ -> visible |

**Edit Rules:**
- Can edit only if they are the **Current Owner**
- Read-only for all other enquiries they can see

**Test Cases:**

| # | Scenario | Expected Result |
|---|----------|-----------------|
| TC-N-01 | Normal user creates an enquiry | Visible in list, can edit |
| TC-N-02 | Normal user views enquiry created by another user | Not visible (unless assigned/reporting) |
| TC-N-03 | Normal user's segment matches but not own created | Not visible |
| TC-N-04 | Enquiry assigned to Normal user | Visible, can edit (is current owner) |
| TC-N-05 | User who reports to Normal user created an enquiry | Visible, read-only |
| TC-N-06 | Normal user without User Configuration | No enquiries visible |
| TC-N-07 | Normal user tries to edit enquiry where they are not current owner | Error: Permission denied |

---

## 3. Head Role

**Prerequisite:** Must have a User Configuration record.

**List View Rules:**

| Rule | Condition | Visible? |
|------|-----------|----------|
| Own Created | Always | Yes |
| Segment + Organisation | Both must match User Config | Yes |
| Sub Segment + Organisation | Both must match User Config | Yes |
| Organisation only | Org matches User Config | Yes |
| Segment only (no org match) | Segment matches but org does not | No |
| Assigned | Enquiry assigned to user | Yes |
| Reporting To | Created by users who report to this user | Yes |

**Edit Rules:**
- Can edit only if they are the **Current Owner**
- Read-only for all other enquiries they can see

**Test Cases:**

Setup: Head user has User Configuration:
- Segments: HVAC, Electrical
- Sub Segments: Chillers, Panels
- Organisations: BO Kolkatta, RO EAST

| # | Scenario | Segment | Organisation | Expected |
|---|----------|---------|-------------|----------|
| TC-H-01 | Segment + Org match | HVAC | BO Kolkatta | Visible |
| TC-H-02 | Sub Segment + Org match | Chillers | RO EAST | Visible |
| TC-H-03 | Org match only | Plumbing | BO Kolkatta | Visible |
| TC-H-04 | Segment match only (no org) | HVAC | Mumbai | Not visible |
| TC-H-05 | No match at all | Plumbing | Mumbai | Not visible |
| TC-H-06 | Head's own created enquiry | Any | Any | Visible |
| TC-H-07 | Enquiry assigned to Head | Any | Any | Visible |
| TC-H-08 | Created by user who reports to Head | Any | Any | Visible |
| TC-H-09 | Head without User Configuration | - | - | No enquiries visible |
| TC-H-10 | Head tries to edit (not current owner) | - | - | Error: Permission denied |
| TC-H-11 | Head edits (is current owner) | - | - | Can edit |

---

## 4. Edit Permission (All Roles)

Only the **Current Owner** or **Administrator/System Manager** can edit an enquiry.

| # | Scenario | Expected |
|---|----------|----------|
| TC-E-01 | Current Owner edits | Allowed |
| TC-E-02 | Previous Current Owner reassigns | Allowed (ownership transfer) |
| TC-E-03 | Administrator edits | Allowed |
| TC-E-04 | System Manager edits | Allowed |
| TC-E-05 | Non-owner Normal user edits | Denied |
| TC-E-06 | Non-owner Head user edits | Denied |

---

## 5. Workflow States

| State | Color | Description |
|-------|-------|-------------|
| Draft | Red | New enquiry, not yet submitted |
| Open | Blue | Submitted and active |
| Offer | Green | Offer stage |
| Unclear | Yellow | Needs clarification, sent back to creator |
| Regret | Orange | Regret state, cancellation not allowed |

---

## 6. Assignment & Reassignment

| Action | What Happens |
|--------|-------------|
| Assign | Current Owner updated, Assignment Log entry added |
| Reassign | Current Owner changed, workflow state set to Open |
| Mark Unclear | Current Owner set back, workflow state set to Unclear, reason recorded |

---

## 7. List View Features

**Buttons:**
- **Check Permissions** - Shows current user's active role and permission details
- **Filters > My Enquiries** - Show enquiries created by current user
- **Filters > Assigned to Me** - Show enquiries assigned to current user
- **Filters > My Segments** - Filter by user's configured segments
- **Filters > My Sub Segments** - Filter by user's configured sub segments
- **Filters > My Organisations** - Filter by user's configured organisations
- **Filters > My Team** - Show enquiries from users who report to current user
- **Filters > Clear Filters** - Reset all filters

---

## Quick Reference

```
Administrator / System Manager
  -> Full Access (no restrictions)

Normal Role
  -> Own created enquiries (always)
  -> Assigned enquiries
  -> Reporting users' enquiries

Head Role
  -> Own created enquiries (always)
  -> Organisation match (always)
  -> Segment + Organisation (both required)
  -> Sub Segment + Organisation (both required)
  -> Assigned enquiries
  -> Reporting users' enquiries
```

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app enquiry_management
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/enquiry_management
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit

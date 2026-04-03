# JJCM API Documentation

Base URL: `https://jjcm.foehst.net`

## Authentication

### POST `/api/auth`

Login to obtain session cookie.

**Request (JSON):**
```json
{
  "username": "<username>",
  "password": "<password>"
}
```

**Response:** Sets `auth_tkt` cookie for subsequent requests.

---

## Competitions

### GET `/api/competitions`

List all competitions.

**Response:**
```json
[
  {
    "id": 8,
    "name": "Deutsche Jiu Jitsu Meisterschaften 2026",
    "date": "2026-05-09",
    "city": "Hochstetten",
    "fee": 12.0,
    "closing_date": "2026-04-11"
  }
]
```

### GET `/api/competitions/{id}`

Get single competition details.

**Response:**
```json
{
  "id": 8,
  "name": "Deutsche Jiu Jitsu Meisterschaften 2026",
  "date": "2026-05-09",
  "city": "Hochstetten",
  "fee": 12.0,
  "closing_date": "2026-04-11"
}
```

---

## Registrations (Competitors)

### GET `/api/competitions/{id}/registrations`

Get competitors registered for an event.

**Query Parameters:**
- `rel=dojo` - Include embedded dojo object

**Response:**
```json
[
  {
    "id": 719,
    "competitor_id": 389,
    "competition_id": 8,
    "given_name": "Aragorn",
    "name": "Starweaver",
    "birthdate": "2006-12-04",
    "age": 19,
    "sex": "MALE",
    "weight": 75.0,
    "rank_id": "ROKKYU",
    "dojo_id": 14,
    "age_class_id": 39,
    "weight_class_id": 197,
    "rank_class_id": 46,
    "dojo": {
      "id": 14,
      "name": "Dragonborn Dojo Mülheim"
    }
  }
]
```

**Fields:**
| Field | Description |
|-------|-------------|
| `id` | Registration ID |
| `competitor_id` | Global competitor ID |
| `competition_id` | Competition this registration belongs to |
| `given_name` | First name |
| `name` | Last name |
| `birthdate` | Date of birth (YYYY-MM-DD) |
| `age` | Calculated age |
| `sex` | `MALE` or `FEMALE` |
| `weight` | Weight in kg (nullable) |
| `rank_id` | Belt rank (e.g., `ROKKYU`, `GOKYU`) |
| `dojo_id` | Reference to dojo |
| `age_class_id` | Age class reference |
| `weight_class_id` | Weight class reference (nullable) |
| `rank_class_id` | Rank class reference |
| `dojo` | Embedded dojo object (when `rel=dojo`) |

---

## Schedule

### GET `/api/competitions/{id}/schedule`

Get the competition schedule with tatamis and time slots.

**Response:**
```json
[
  {
    "day": "Samstag",
    "tatami": [
      {
        "begin": 60,
        "items": [
          {
            "begin": 60,
            "duration": 27,
            "categoryId": 188,
            "discipline": "RandomAttack",
            "categoryName": "Erwachsene, blau/braun",
            "cardinality": 4,
            "competitors": [670, 661, 673, 676],
            "type": "pre",
            "numberOfGames": 6,
            "timePerGame": 4.5,
            "conflict": false
          },
          {
            "begin": 87,
            "duration": 3,
            "id": "pause-...",
            "conflict": false
          }
        ]
      }
    ]
  }
]
```

**Schedule Item Fields:**
| Field | Description |
|-------|-------------|
| `begin` | Start time in minutes (offset from 9:00 AM) |
| `duration` | Duration in minutes |
| `categoryId` | Category reference |
| `discipline` | Discipline name (e.g., `RandomAttack`, `Team`) |
| `categoryName` | Human-readable category name |
| `cardinality` | Number of competitors |
| `competitors` | Array of competitor IDs |
| `type` | Phase type (`pre`, `final`) |
| `numberOfGames` | Number of games in this slot |
| `timePerGame` | Minutes per game |
| `conflict` | Scheduling conflict flag |

**Pause Items:**
- Have `id` starting with `pause-`
- Only contain `begin`, `duration`, `id`, `conflict`

---

## Categories

### GET `/api/competitions/{id}/categories`

Get categories for a competition.

**Response:**
```json
[]
```

---

## Dojos

### GET `/api/dojos`

List all dojos (may return empty depending on user permissions).

**Response:**
```json
[
  {
    "id": 14,
    "name": "Dragonborn Dojo Mülheim"
  }
]
```

---

## Competitors

### GET `/api/competitors`

List competitors (may return empty depending on user permissions).

---

## Environment Variables

The application uses these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `JJCM_BASE` | `https://jjcm.foehst.net` | API base URL |
| `JJCM_USERNAME` | - | Login username |
| `JJCM_PASSWORD` | - | Login password |

---

## JJCM API Entity-Relationship Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              COMPETITION                                     │
│  id, name, date, city, fee, closing_date                                    │
└─────────────────────────────────────────────────────────────────────────────┘
        │                              │
        │ 1:N                          │ 1:N
        ▼                              ▼
┌───────────────────────────┐    ┌─────────────────────────┐
│       REGISTRATION        │    │        SCHEDULE         │
│  id (registration_id)     │    │   day, tatami[]         │
│  competitor_id            │    └─────────────────────────┘
│  competition_id           │                │
│  given_name, name         │                │ contains
│  birthdate, age, sex      │                ▼
│  weight                   │    ┌─────────────────────────┐
│  rank_id                  │    │      SCHEDULE ITEM      │
│  dojo_id ─────────────────┼─┐  │  categoryId, discipline │
│  age_class_id             │ │  │  categoryName, begin,   │
│  weight_class_id          │ │  │  duration, type         │
│  rank_class_id            │ │  │  competitors[] ─────────┼──┐
└───────────────────────────┘ │  └─────────────────────────┘  │
        ▲                     │                               │
        │                     │    N:M (competitors[] refs    │
        │ N:1                 │    Registration.id)           │
        └─────────────────────┼───────────────────────────────┘
                              │
                              │ N:1
                              ▼
              ┌───────────────────────────┐
              │           DOJO            │
              │  id, name                 │
              └───────────────────────────┘
```

### Key Relationships (API)

| From | To | Relationship | Join Field |
|------|-----|--------------|------------|
| Registration | Competition | N:1 | `competition_id` |
| Registration | Dojo | N:1 | `dojo_id` |
| Schedule Item | Registration | N:M | `competitors[]` contains `Registration.id` |

---

## Local Database Entity-Relationship Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              COMPETITION                                     │
│  id, title, description, location, firstDay, lastDay, active                │
│  jjcmCompetitionId, jjcmHash                                                │
└─────────────────────────────────────────────────────────────────────────────┘
        │                              │
        │ 1:N                          │ 1:N
        ▼                              ▼
┌───────────────────────────┐    ┌─────────────────────────────────────────┐
│       REGISTRATION        │    │               SLOT (polymorphic)        │
│  id                       │    │  id, start, end, title, competition_id  │
│  competitor_id (FK) ──────┼─┐  ├─────────────────────────────────────────┤
│  competition_id (FK)      │ │  │         EXTERNALPROVIDEDSLOT            │
│  dojo_id (FK) ────────────┼─┼─┐│  hash, discipline, category_name        │
│  jjcmRegistrationId       │ │ ││  type, tatami                           │
│  jjcmAgeClassId           │ │ ││  registrations (M:N) ───────────────────┼──┐
│  jjcmWeightClassId        │ │ │└─────────────────────────────────────────┘  │
│  jjcmRankClassId          │ │ │                                             │
│  jjcmRankId               │ │ │                                             │
│  hash                     │ │ │                                             │
└───────────────────────────┘ │ │                                             │
        ▲                     │ │                                             │
        │                     │ │         M:N                                 │
        └─────────────────────┼─┼─────────────────────────────────────────────┘
                              │ │
                              │ │ N:1
                              ▼ ▼
┌───────────────────────────┐ ┌───────────────────────────┐
│        COMPETITOR         │ │           DOJO            │
│  id                       │ │  id                       │
│  name, givenName, sex     │ │  name                     │
│  jjcmCompetitorId (unique)│ │  jjcmDojoId               │
└───────────────────────────┘ └───────────────────────────┘

┌───────────────────────────┐
│           RANK            │
│  ID (PK), name, color     │
│  rankClass, kyu, dan      │
└───────────────────────────┘
```

### Key Relationships (Local DB)

| From | To | Relationship | Join Field |
|------|-----|--------------|------------|
| Registration | Competitor | N:1 | `competitor_id` |
| Registration | Competition | N:1 | `competition_id` |
| Registration | Dojo | N:1 | `dojo_id` |
| ExternalProvidedSlot | Competition | N:1 | `competition_id` |
| ExternalProvidedSlot | Registration | M:N | `registrations` |

### Mapping: JJCM API → Local DB

| JJCM API | Local Model | Notes |
|----------|-------------|-------|
| Competition | Competition | `id` → `jjcmCompetitionId` |
| Registration | Registration | `id` → `jjcmRegistrationId` |
| Registration.competitor_id | Competitor | `competitor_id` → `jjcmCompetitorId` |
| Dojo | Dojo | `id` → `jjcmDojoId` |
| Schedule Item | ExternalProvidedSlot | Linked via `registrations` M:N |
| (person fields) | Competitor | `given_name`, `name`, `sex` |
| (competition fields) | Registration | `rank_id`, `dojo_id`, `age_class_id`, etc. |

### ID Clarification

- **`Registration.jjcmRegistrationId`**: The `id` from JJCM `/registrations` (used in schedule `competitors[]`)
- **`Competitor.jjcmCompetitorId`**: The `competitor_id` from JJCM (same person across competitions)

### Belt Ranks (rank_id)

| Value | Meaning |
|-------|---------|
| HAKKYU | 8th Kyu (white/yellow) |
| NANAKYU | 7th Kyu |
| ROKKYU | 6th Kyu (green) |
| GOKYU | 5th Kyu |
| YONKYU | 4th Kyu (blue) |
| IKKYU | 1st Kyu (brown) |
| SHODAN | 1st Dan (black) |
| NIDAN | 2nd Dan |
| SANDAN | 3rd Dan |
| YONDAN | 4th Dan |

### Disciplines

- `RandomAttack` - Defense against random attacks
- `GroundFighting` - Ground combat (weight classes)
- `GroundFightingOpen` - Ground combat (open weight)
- `Pairs` - Partner techniques
- `Kata` - Form demonstrations
- `Team` - Team competition

---

## Sample Data

Sample JSON responses are stored in `jjcm_samples/`:

| File | Endpoint | Description |
|------|----------|-------------|
| `competitions.json` | `/api/competitions` | List of all 4 competitions |
| `competition_single.json` | `/api/competitions/9` | Single competition details |
| `registrations.json` | `/api/competitions/9/registrations?rel=dojo` | 44 competitors with dojo info |
| `registrations_comp6.json` | `/api/competitions/6/registrations?rel=dojo` | 123 competitors (largest dataset) |
| `schedule.json` | `/api/competitions/9/schedule` | 2-day schedule (Samstag, Sonntag) with 3 tatamis |
| `schedule_comp7.json` | `/api/competitions/7/schedule` | 2-day schedule for competition 7 |
| `categories.json` | `/api/competitions/9/categories` | Empty array (categories not exposed via API) |
| `dojos.json` | `/api/dojos` | Empty array (permission-dependent) |
| `competitors.json` | `/api/competitors` | Empty array (permission-dependent) |

### Data Availability by Competition

| ID | Name | Registrations | Schedule |
|----|------|---------------|----------|
| 6 | Deutsche Jiu Jitsu Meisterschaften 2024 | 123 | not found |
| 7 | Vereinsmeisterschaften - TV Hochstetten | 16 | 2 days |
| 8 | Deutsche Jiu Jitsu Meisterschaften 2026 | 108 | null |
| 9 | Spielplatz | 44 | 2 days |

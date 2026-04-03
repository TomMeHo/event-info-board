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

### GET `/api/competitions/{id}/select`

**Required before fetching categories.** Selects a competition for the current session.

**Response:** `200 OK`

### GET `/api/competitions/{id}/{discipline}/categories`

Get categories for a specific discipline. Requires competition to be selected first.

**Disciplines:**
- `random_attack`
- `ground_fighting`
- `ground_fighting_open`
- `pairs`
- `kata`
- `team`

**Response:**
```json
[
  {
    "name": "Erwachsene, grün",
    "category": {
      "discipline": "RandomAttack",
      "sex": [],
      "age_class": [
        {
          "min": 18,
          "difficulty": 3,
          "id": 44,
          "short": "C",
          "competition_id": 9,
          "name": "Erwachsene"
        }
      ],
      "weight_class": [],
      "rank_class": [
        {
          "id": 52,
          "css_color": "white",
          "competition_id": 9,
          "css_background": "green",
          "name": "grün"
        }
      ],
      "rank": [],
      "name": "Erwachsene, grün",
      "id": 192,
      "has_games": true
    },
    "cardinality": 13,
    "avg_age": 21.0,
    "min_age": 18,
    "max_age": 25,
    "avg_rank": 7.0,
    "entries": [
      {
        "competitor_registration_id": 682,
        "override_category_id": null,
        "competition_id": 9,
        "dojo_id": 22,
        "id": 975,
        "type": "random_attack_entry"
      }
    ]
  }
]
```

**Category Fields:**
| Field | Description |
|-------|-------------|
| `name` | Human-readable category name |
| `category.id` | Category ID (may be null for auto-generated categories) |
| `category.discipline` | Discipline enum value |
| `category.age_class` | Array of age class objects |
| `category.weight_class` | Array of weight class objects (for ground fighting) |
| `category.rank_class` | Array of rank class objects (for random attack, pairs) |
| `category.has_games` | Whether games have been scheduled |
| `cardinality` | Number of entries in this category |
| `entries` | Array of entry objects with registration references |

---

## Entries

### GET `/api/competitions/{id}/{discipline}/entries`

Get entries (discipline registrations) for a competition. Requires competition to be selected first.

**Disciplines:** `random_attack`, `ground_fighting`, `ground_fighting_open`, `pairs`, `kata`, `team`

**Query Parameters:**
- `rel=members` - Include team members (for team discipline)

**Response (random_attack, ground_fighting, ground_fighting_open):**
```json
[
  {
    "id": 975,
    "type": "random_attack_entry",
    "competition_id": 9,
    "dojo_id": 22,
    "competitor_registration_id": 682,
    "override_category_id": null
  }
]
```

**Response (pairs):**
```json
[
  {
    "id": 1038,
    "type": "pairs_entry",
    "competition_id": 9,
    "dojo_id": 22,
    "competitor_a_registration_id": 682,
    "competitor_b_registration_id": 684,
    "override_category_id": null
  }
]
```

**Response (kata):**
```json
[
  {
    "id": 1048,
    "type": "kata_entry",
    "competition_id": 9,
    "dojo_id": 22,
    "tori_registration_id": 677,
    "uke_registration_id": 701,
    "override_category_id": null
  }
]
```

**Response (team with rel=members):**
```json
[
  {
    "id": 1053,
    "type": "team_entry",
    "competition_id": 9,
    "dojo_id": 22,
    "comment": null,
    "override_category_id": null,
    "members": [
      {
        "id": 669,
        "competitor_id": 95,
        "given_name": "Oliver",
        "name": "Becker",
        "rank_id": "SHODAN"
      }
    ]
  }
]
```

**Entry Fields by Type:**
| Type | Fields |
|------|--------|
| Single competitor | `competitor_registration_id` |
| Pairs | `competitor_a_registration_id`, `competitor_b_registration_id` |
| Kata | `tori_registration_id`, `uke_registration_id` |
| Team | `members[]` (array of registration objects), `comment` |

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
│  jjcmCompetitionId, jjcmHash, jjcmEntriesHash, jjcmCategoriesHash          │
└─────────────────────────────────────────────────────────────────────────────┘
        │                              │                              │
        │ 1:N                          │ 1:N                          │ 1:N
        ▼                              ▼                              ▼
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

┌───────────────────────────┐  ┌───────────────────────────────────────────┐
│           RANK            │  │                CATEGORY                    │
│  ID (PK), name, color     │  │  id, competition_id (FK)                  │
│  rankClass, mon, kyu, dan │  │  jjcmCategoryId, name, discipline         │
└───────────────────────────┘  │  ageClassName, ageClassId, ageClassMin    │
                               │  weightClassName, weightClassId           │
                               │  rankClassName, rankClassId               │
                               │  cardinality, hasGames                    │
                               └───────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENTRY (polymorphic)                                │
│  id, competition_id (FK), dojo_id (FK), category_id (FK)                    │
│  jjcmEntryId, overrideCategoryId                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  SINGLECOMPETITORENTRY         │  discipline, competitor_id (FK)            │
├────────────────────────────────┼────────────────────────────────────────────┤
│  PAIRSENTRY                    │  competitor_a_id (FK), competitor_b_id (FK)│
├────────────────────────────────┼────────────────────────────────────────────┤
│  KATAENTRY                     │  tori_id (FK), uke_id (FK)                 │
├────────────────────────────────┼────────────────────────────────────────────┤
│  TEAMENTRY                     │  members (M:N to Registration), comment    │
└────────────────────────────────┴────────────────────────────────────────────┘
```

### Key Relationships (Local DB)

| From | To | Relationship | Join Field |
|------|-----|--------------|------------|
| Registration | Competitor | N:1 | `competitor_id` |
| Registration | Competition | N:1 | `competition_id` |
| Registration | Dojo | N:1 | `dojo_id` |
| ExternalProvidedSlot | Competition | N:1 | `competition_id` |
| ExternalProvidedSlot | Registration | M:N | `registrations` |
| Category | Competition | N:1 | `competition_id` |
| Entry | Competition | N:1 | `competition_id` |
| Entry | Dojo | N:1 | `dojo_id` |
| Entry | Category | N:1 | `category_id` |
| SingleCompetitorEntry | Registration | N:1 | `competitor_id` |
| PairsEntry | Registration | N:1 | `competitor_a_id`, `competitor_b_id` |
| KataEntry | Registration | N:1 | `tori_id`, `uke_id` |
| TeamEntry | Registration | M:N | `members` |

### Mapping: JJCM API → Local DB

| JJCM API | Local Model | Notes |
|----------|-------------|-------|
| Competition | Competition | `id` → `jjcmCompetitionId` |
| Registration | Registration | `id` → `jjcmRegistrationId` |
| Registration.competitor_id | Competitor | `competitor_id` → `jjcmCompetitorId` |
| Dojo | Dojo | `id` → `jjcmDojoId` |
| Schedule Item | ExternalProvidedSlot | Linked via `registrations` M:N |
| Category | Category | `category.id` → `jjcmCategoryId` |
| Entry | Entry (polymorphic) | `id` → `jjcmEntryId` |
| (person fields) | Competitor | `given_name`, `name`, `sex` |
| (competition fields) | Registration | `rank_id`, `dojo_id`, `age_class_id`, etc. |

### ID Clarification

- **`Registration.jjcmRegistrationId`**: The `id` from JJCM `/registrations` (used in schedule `competitors[]`)
- **`Competitor.jjcmCompetitorId`**: The `competitor_id` from JJCM (same person across competitions)

### Belt Ranks (rank_id)

| Value | Meaning | Color |
|-------|---------|-------|
| HAKKYU | 8th Kyu | gelb (yellow) |
| NANAKYU | 7th Kyu | orange |
| ROKKYU | 6th Kyu | grün (green) |
| GOKYU | 5th Kyu | blau (blue) |
| YONKYU | 4th Kyu | braun (brown) |
| SANKYU | 3rd Kyu | braun + 1 Streifen |
| NIKYU | 2nd Kyu | braun + 2 Streifen |
| IKKYU | 1st Kyu | braun + 3 Streifen |
| SHODAN | 1st Dan | schwarz (black) |
| NIDAN | 2nd Dan | schwarz |
| SANDAN | 3rd Dan | schwarz |
| YONDAN | 4th Dan | schwarz |
| GODAN | 5th Dan | schwarz |
| ROKUDAN | 6th Dan | rot-weiß (red-white) |
| SHICHIDAN | 7th Dan | rot-weiß |
| HACHIDAN | 8th Dan | rot-weiß |
| KUDAN | 9th Dan | rot (red) |
| JUDAN | 10th Dan | rot |

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

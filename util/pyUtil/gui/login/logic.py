"""Who works at this Olex2, and filling in a structure's operator.

The user is identified by user.email in DataDir's user.phil: one DataDir per
PC user account. People are matched by email, never by row id, because row
ids differ between databases. Plain functions on an sqlite connection, so
they can be tested without Olex2.
"""

EMPTY = ('', '?', "''", '""', '.', 'None')


def is_empty(value):
  return value is None or str(value).strip() in EMPTY


def normalise_email(email):
  return (email or '').strip().lower()


def valid_email(email):
  email = normalise_email(email)
  local, at, domain = email.partition('@')
  return bool(local and at and '.' in domain.strip('.') and ' ' not in email)


def people_with_email(conn, email):
  email = normalise_email(email)
  if not email:
    return []
  rows = conn.execute(
    "SELECT id FROM person WHERE lower(trim(email)) = ? ORDER BY id", (email,))
  return [r[0] for r in rows.fetchall()]


def find_user(conn, email):
  """(person id or None, status); status is 'found', 'missing', 'duplicate'
  (several people share the email, so none is picked) or 'no_email'."""
  if not normalise_email(email):
    return None, 'no_email'
  ids = people_with_email(conn, email)
  if len(ids) == 1:
    return ids[0], 'found'
  return None, ('duplicate' if ids else 'missing')


def find_affiliation(conn, name):
  name = (name or '').strip().lower()
  if not name:
    return None
  row = conn.execute(
    "SELECT id FROM affiliation WHERE lower(trim(name)) = ? ORDER BY id", (name,)).fetchone()
  return row[0] if row else None


def add_user(conn, email, firstname, lastname, affiliation_id=None,
             affiliation_name='', middlename='', phone='', orcid=''):
  """Add the person (and the affiliation, if it is new) and return the person
  id. If the email is already known, that person is returned unchanged.
  Raises ValueError with a message for the form."""
  email = normalise_email(email)
  firstname, lastname = (firstname or '').strip(), (lastname or '').strip()
  if not valid_email(email):
    raise ValueError("Please enter a valid email address")
  if not (firstname and lastname):
    raise ValueError("Please enter your first and last name")
  pid, status = find_user(conn, email)
  if status == 'found':
    return pid
  if status == 'duplicate':
    raise ValueError("Several people in the database have this email: "
                     "please sort that out in 'Manage users' first")
  if is_empty(affiliation_id):
    affiliation_id = None
  if affiliation_id is None:
    affiliation_id = find_affiliation(conn, affiliation_name)
    if affiliation_id is None and not (affiliation_name or '').strip():
      raise ValueError("Please choose your institution or enter a new one")
  with conn:
    if affiliation_id is None:
      affiliation_id = conn.execute(
        "INSERT INTO affiliation (name) VALUES (?)",
        (affiliation_name.strip(),)).lastrowid
    return conn.execute(
      "INSERT INTO person (affiliationid, firstname, middlename, lastname,"
      " email, phone, orchid_id, add_author) VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
      (int(affiliation_id), firstname, (middlename or '').strip(), lastname,
       email, (phone or '').strip(), (orcid or '').strip())).lastrowid


def people_items(conn):
  """[(person id, 'Lastname, Firstname - email')] for 'I am already listed'."""
  rows = conn.execute(
    "SELECT id, firstname, lastname, email FROM person"
    " ORDER BY lower(lastname), lower(firstname)").fetchall()
  items = []
  for pid, first, last, email in rows:
    name = ', '.join(p for p in ((last or '').strip(), (first or '').strip()) if p)
    if not name:
      continue
    email = (email or '').strip()
    items.append((pid, '%s - %s' % (name, email) if email else name))
  return items


def person_fields(conn, person_id):
  """The form's fields for a person in the database, or None."""
  row = conn.execute(
    "SELECT email, firstname, lastname, affiliationid, phone, orchid_id"
    " FROM person WHERE id = ?", (int(person_id),)).fetchone()
  if not row:
    return None
  keys = ('email', 'firstname', 'lastname', 'affiliation', 'phone', 'orcid')
  return {k: ('' if v is None else str(v).strip()) for k, v in zip(keys, row)}


def claim_person(conn, person_id, email):
  """The user says they are this person: from now on they log in with this
  email, which is written to the person if it differs. Returns the person
  id; raises ValueError with a message for the form."""
  person_id = int(person_id)
  email = normalise_email(email)
  if not valid_email(email):
    raise ValueError("Please enter a valid email address")
  if not conn.execute("SELECT 1 FROM person WHERE id = ?", (person_id,)).fetchone():
    raise ValueError("This person is no longer in the database")
  if [i for i in people_with_email(conn, email) if i != person_id]:
    raise ValueError("This email belongs to someone else in the database")
  with conn:
    conn.execute("UPDATE person SET email = ? WHERE id = ?"
                 " AND lower(trim(coalesce(email, ''))) != ?",
                 (email, person_id, email))
  return person_id


def operator_changes(user_id, user_name, operator, contact_name):
  """What to fill in for a structure: 'operator' ('Solved by', a person id)
  and 'contact' (the CIF contact author, a name) are one person, the
  logged-in user. Only empty values are filled in; nothing is overwritten."""
  changes = {}
  if user_id is None:
    return changes
  if is_empty(operator):
    changes['operator'] = str(user_id)
  if is_empty(contact_name) and user_name:
    changes['contact'] = user_name
  return changes

from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import Course, Lecture, Question, Topic

QUESTIONS = [
    ('Relational databases', 'What does a primary key identify?', ['A unique row', 'Every table', 'A database server', 'A query result'], 0, 'A primary key uniquely identifies each row in its table.'),
    ('Relational databases', 'What does a foreign key enforce?', ['Alphabetical sorting', 'Referential integrity', 'Password strength', 'File compression'], 1, 'A foreign key requires references to match a key in the related table, unless null is allowed.'),
    ('Relational databases', 'Which SQL clause filters rows before grouping?', ['ORDER BY', 'HAVING', 'WHERE', 'GROUP BY'], 2, 'WHERE filters individual rows. HAVING filters groups after aggregation.'),
    ('Relational databases', 'Which join retains every row from the left table?', ['INNER JOIN', 'CROSS JOIN', 'RIGHT JOIN', 'LEFT JOIN'], 3, 'LEFT JOIN retains left-table rows even if there is no matching right-table row.'),
    ('Transactions', 'What does atomicity mean?', ['All operations succeed or all are rolled back', 'Every query is fast', 'Data is always encrypted', 'Only one table is allowed'], 0, 'Atomicity makes a transaction an all-or-nothing unit of work.'),
    ('Transactions', 'Which ACID property keeps committed data after a restart?', ['Isolation', 'Durability', 'Atomicity', 'Consistency'], 1, 'Durability means a committed transaction survives a system restart.'),
    ('Transactions', 'What is the purpose of ROLLBACK?', ['Create a table', 'Sort rows', 'Undo uncommitted changes', 'Add an index'], 2, 'ROLLBACK cancels the uncommitted changes of the current transaction.'),
    ('Transactions', 'What does isolation regulate?', ['Column naming', 'File size', 'Password length', 'Interactions between concurrent transactions'], 3, 'Isolation controls how concurrent transactions observe and affect each other.'),
    ('Indexes & design', 'What is a common tradeoff of adding an index?', ['Faster reads but extra storage and write work', 'No disk use', 'All writes become faster', 'All duplicates disappear'], 0, 'An index can accelerate lookups but takes space and must be maintained on writes.'),
    ('Indexes & design', 'Why normalize a relational schema?', ['Remove every relationship', 'Reduce redundancy and update anomalies', 'Replace all keys with text', 'Prevent all joins'], 1, 'Normalization organizes dependencies to reduce redundant facts and inconsistent updates.'),
    ('Indexes & design', 'Which structure commonly supports database indexes?', ['A stack of images', 'An audio buffer', 'A B-tree', 'A video stream'], 2, 'B-tree indexes support efficient ordered lookups and range searches.'),
    ('Indexes & design', 'How is a many-to-many relationship commonly represented?', ['One comma-separated column', 'A duplicated database', 'An unconnected table', 'A junction table with foreign keys'], 3, 'A junction table stores pairs of references to link rows in the two related tables.'),
]

@transaction.atomic
def create_demo(user):
    course = Course.objects.filter(owner=user, name='Database Fundamentals · Demo').first()
    if course:
        return course
    course = Course.objects.create(owner=user, name='Database Fundamentals · Demo', exam_date=timezone.localdate() + timedelta(days=30))
    lecture = Lecture.objects.create(course=course, title='Database foundations — demo material', original_name='Built-in demo',
        text='\n'.join(row[4] for row in QUESTIONS), generated=True)
    for name, prompt, choices, answer, explanation in QUESTIONS:
        topic, _ = Topic.objects.get_or_create(course=course, name=name)
        Question.objects.create(topic=topic, lecture=lecture, prompt=prompt, choices=choices, correct_index=answer, explanation=explanation)
    return course

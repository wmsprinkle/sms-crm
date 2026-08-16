from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, JSON, Text


class Base(DeclarativeBase):
    pass


class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String, unique=True, index=True)      # E.164
    first_name: Mapped[str | None] = mapped_column(String)
    fields: Mapped[dict] = mapped_column(JSON, default=dict)                 # merge data + tags
    timezone: Mapped[str] = mapped_column(String, default="America/New_York")
    status: Mapped[str] = mapped_column(String, default="new")              # new|active|engaged|booked|opted_out
    opted_out: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str | None] = mapped_column(String)                      # which CSV import
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Sequence(Base):
    __tablename__ = "sequences"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    steps: Mapped[list["Step"]] = relationship(back_populates="sequence",
                                               order_by="Step.order")


class Step(Base):
    __tablename__ = "steps"
    id: Mapped[int] = mapped_column(primary_key=True)
    sequence_id: Mapped[int] = mapped_column(ForeignKey("sequences.id"))
    order: Mapped[int] = mapped_column(Integer)                             # 0,1,2...
    delay_minutes: Mapped[int] = mapped_column(Integer)                     # wait after previous step
    body: Mapped[str] = mapped_column(Text)                                 # "Hi {{first_name}}, ..."
    sequence: Mapped["Sequence"] = relationship(back_populates="steps")


class Enrollment(Base):
    __tablename__ = "enrollments"
    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), index=True)
    sequence_id: Mapped[int] = mapped_column(ForeignKey("sequences.id"))
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="active")          # active|paused|completed|booked|opted_out
    next_send_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), index=True)
    direction: Mapped[str] = mapped_column(String)                         # in|out
    body: Mapped[str] = mapped_column(Text)
    telnyx_id: Mapped[str | None] = mapped_column(String, index=True)
    status: Mapped[str | None] = mapped_column(String)                    # draft|queued|sent|delivered|failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), index=True)
    provider: Mapped[str] = mapped_column(String)                         # calendly|calcom|static
    event_uri: Mapped[str | None] = mapped_column(String)
    scheduled_time: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default="booked")         # booked|canceled
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

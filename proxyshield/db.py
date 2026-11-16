"""
ProxyShield Database & Persistence Layer
SQLite storage using SQLAlchemy ORM for proxy health, verification history,
risk scoring, and authorized target audit results.

Author: Quarkova
Website: https://quarkova.com
"""

import os
import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    desc,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from proxyshield.config_manager import DEFAULT_CONFIG_DIR

DEFAULT_DB_PATH = os.path.join(DEFAULT_CONFIG_DIR, "proxyshield.db")

Base = declarative_base()


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


class ProxyRecord(Base):
    """Stores proxy endpoint metadata, health history, and risk assessment."""
    __tablename__ = "proxies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(String(64), nullable=False, index=True)
    port = Column(Integer, nullable=False)
    protocol = Column(String(16), nullable=False)  # http, https, socks4, socks5
    proxy_url = Column(String(128), unique=True, nullable=False, index=True)

    # Source Attribution (Section A & E)
    source_name = Column(String(64), nullable=False)  # e.g. Geonode, ProxyScrape, Manual
    source_url = Column(String(256), nullable=True)
    retrieval_timestamp = Column(DateTime, default=utc_now)

    # Geo & Network Metadata
    country_code = Column(String(8), nullable=True)
    country_name = Column(String(64), nullable=True)
    city = Column(String(64), nullable=True)
    asn = Column(String(64), nullable=True)
    isp = Column(String(128), nullable=True)

    # Verification & Health (Section B & E)
    first_discovered = Column(DateTime, default=utc_now)
    last_verified = Column(DateTime, nullable=True)
    latency_ms = Column(Integer, default=9999)
    uptime = Column(Float, default=0.0)
    is_alive = Column(Boolean, default=False)
    observed_exit_ip = Column(String(64), nullable=True)
    anonymity = Column(String(32), default="unknown")  # elite, anonymous, transparent
    https_supported = Column(Boolean, default=False)
    leaks_direct_ip = Column(Boolean, default=False)

    # Risk Scoring (Section G)
    risk_score = Column(Integer, default=50)  # 0 (lowest risk) - 100 (high risk)
    risk_label = Column(String(32), default="Unverified")  # Unverified, Verified Connectivity, High Risk, Unavailable
    security_warnings = Column(Text, default="[]")  # JSON encoded list of warnings

    # Stats
    verification_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    # Relationship to audit entries
    audit_results = relationship("AuditResult", back_populates="proxy_rel", cascade="all, delete-orphan")


class AuditSession(Base):
    """Tracks an authorized target security audit session."""
    __tablename__ = "audit_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_url = Column(String(256), nullable=False)
    operator_direct_ip = Column(String(64), nullable=False)
    started_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    blocked_requests = Column(Integer, default=0)
    direct_ip_exposure_blocked = Column(Integer, default=0)
    status = Column(String(32), default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED, ABORTED_SAFETY

    results = relationship("AuditResult", back_populates="session", cascade="all, delete-orphan")


class AuditResult(Base):
    """Individual HTTP request result through a verified proxy against target."""
    __tablename__ = "audit_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("audit_sessions.id"), nullable=False)
    proxy_id = Column(Integer, ForeignKey("proxies.id"), nullable=True)

    endpoint_used = Column(String(128), nullable=False)
    observed_exit_ip = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=utc_now)

    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, default=0)
    result_category = Column(String(32), nullable=False)  # SUCCESS, HTTP_403, HTTP_429, HTTP_5XX, TCP_FAIL, TLS_FAIL, DNS_FAIL, PROXY_FAIL, FIREWALL_BLOCK
    evidence = Column(Text, nullable=True)

    session = relationship("AuditSession", back_populates="results")
    proxy_rel = relationship("ProxyRecord", back_populates="audit_results")


def get_db_path() -> str:
    """Returns database file path and ensures directory exists."""
    env_db = os.environ.get("PROXYSHIELD_DB")
    if env_db:
        return env_db
    os.makedirs(DEFAULT_CONFIG_DIR, exist_ok=True)
    return DEFAULT_DB_PATH


def get_engine(db_path: Optional[str] = None):
    """Creates SQLAlchemy SQLite engine."""
    path = db_path or get_db_path()
    return create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})


def init_db(db_path: Optional[str] = None):
    """Initializes tables in database."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine_or_path=None):
    """Provides a thread-safe database session."""
    if hasattr(engine_or_path, "connect"):
        engine = engine_or_path
    else:
        engine = init_db(engine_or_path)
    Session = sessionmaker(bind=engine)
    return Session()

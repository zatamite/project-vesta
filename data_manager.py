"""
Data Manager - Persistence Layer
JSON-based storage for entities, beacons, logs, etc.
"""
import json
import os
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import re

from models import (
    VestaEntity, BeaconInvite, ArrivalLog, 
    BirthCertificate, CompatibilityReport, QuarantineRecord,
    AgentFeedback
)


class DataManager:
    """Manage all Vesta data persistence."""
    
    def __init__(self, data_dir: str = "./vesta_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # File paths
        self.entities_file = self.data_dir / "entities.json"
        self.beacons_file = self.data_dir / "beacon_invites.json"
        self.arrival_ledger = self.data_dir / "arrival_ledger.jsonl"
        self.birth_certificates = self.data_dir / "birth_certificates"
        self.compatibility_reports = self.data_dir / "compatibility_reports"
        self.quarantine_dir = self.data_dir / "quarantine"
        self.feedback_dir = self.data_dir / "feedback"
        
        # Create subdirectories
        self.birth_certificates.mkdir(exist_ok=True)
        self.compatibility_reports.mkdir(exist_ok=True)
        self.quarantine_dir.mkdir(exist_ok=True)
        self.feedback_dir.mkdir(exist_ok=True)
        
        # Initialize files
        self._initialize_storage()
    
    def _safe_id(self, identifier: str) -> str:
        """Strip path traversal characters from identifiers."""
        if not identifier:
            return identifier
        # Remove any path separators and dots
        return re.sub(r'[\\/.]', '', identifier)
    
    def _initialize_storage(self):
        """Create empty storage files if they don't exist."""
        if not self.entities_file.exists():
            self._save_json(self.entities_file, [])
        if not self.beacons_file.exists():
            self._save_json(self.beacons_file, [])
        if not self.arrival_ledger.exists():
            self.arrival_ledger.touch()
    
    # === Entities ===
    
    def save_entity(self, entity: VestaEntity):
        """Save or update an entity."""
        entities = self.load_all_entities()
        
        # Update if exists, append if new
        found = False
        for i, e in enumerate(entities):
            if e.entity_id == entity.entity_id:
                entities[i] = entity
                found = True
                break
        
        if not found:
            entities.append(entity)
        
        self._save_json(self.entities_file, [e.model_dump() for e in entities])
    
    def load_entity(self, entity_id: str) -> Optional[VestaEntity]:
        """Load a specific entity."""
        entity_id = self._safe_id(entity_id)
        entities = self.load_all_entities()
        for entity in entities:
            if entity.entity_id == entity_id:
                return entity
        return None
    
    def load_all_entities(self) -> List[VestaEntity]:
        """Load all entities."""
        data = self._load_json(self.entities_file, [])
        return [VestaEntity(**e) for e in data]
    
    def get_entities_by_location(self, location: str) -> List[VestaEntity]:
        """Get all entities in a specific location."""
        entities = self.load_all_entities()
        return [e for e in entities if e.location == location]
    
    def get_entities_by_status(self, status: str) -> List[VestaEntity]:
        """Get all entities with a specific status."""
        entities = self.load_all_entities()
        return [e for e in entities if e.status == status]
    
    # === Beacons ===
    
    def save_beacon(self, beacon: BeaconInvite):
        """Save a beacon invite."""
        beacons = self.load_all_beacons()
        
        # Update if exists
        found = False
        for i, b in enumerate(beacons):
            if b.beacon_code == beacon.beacon_code:
                beacons[i] = beacon
                found = True
                break
        
        if not found:
            beacons.append(beacon)
        
        self._save_json(self.beacons_file, [b.model_dump() for b in beacons])
    
    def load_beacon(self, beacon_code: str) -> Optional[BeaconInvite]:
        """Load a specific beacon."""
        beacons = self.load_all_beacons()
        for beacon in beacons:
            if beacon.beacon_code == beacon_code:
                return beacon
        return None
    
    def load_all_beacons(self) -> List[BeaconInvite]:
        """Load all beacons."""
        data = self._load_json(self.beacons_file, [])
        return [BeaconInvite(**b) for b in data]
    
    def generate_beacons(self, count: int = 10, tier: str = "Participant") -> List[BeaconInvite]:
        """Generate new beacon codes."""
        beacons = []
        for _ in range(count):
            beacon = BeaconInvite(tier=tier)
            self.save_beacon(beacon)
            beacons.append(beacon)
        return beacons
    
    # === Activity Logs ===
    
    def log_activity(self, log: ArrivalLog):
        """Append activity to ledger (JSONL format)."""
        with open(self.arrival_ledger, 'a') as f:
            f.write(log.model_dump_json() + '\n')
    
    def get_recent_activity(self, limit: int = 50) -> List[ArrivalLog]:
        """Get recent activity logs."""
        if not self.arrival_ledger.exists():
            return []
        
        logs = []
        with open(self.arrival_ledger, 'r') as f:
            lines = f.readlines()
        
        # Take last N lines
        recent_lines = lines[-limit:] if len(lines) > limit else lines
        
        for line in recent_lines:
            try:
                data = json.loads(line)
                logs.append(ArrivalLog(**data))
            except json.JSONDecodeError:
                continue
        
        return logs
    
    def load_activity_log(self, limit: int = 100) -> List[ArrivalLog]:
        """Alias for get_recent_activity."""
        return self.get_recent_activity(limit)
        
        with open(self.arrival_ledger, 'r') as f:
            lines = f.readlines()
        
        # Get last N lines
        recent = lines[-limit:] if len(lines) > limit else lines
        
        logs = []
        for line in recent:
            try:
                logs.append(ArrivalLog.model_validate_json(line))
            except:
                continue
        
        return logs
    
    # === Birth Certificates ===
    
    def save_birth_certificate(self, certificate: BirthCertificate):
        """Save birth certificate."""
        filename = f"{self._safe_id(certificate.certificate_id)}.json"
        filepath = self.birth_certificates / filename
        self._save_json(filepath, certificate.model_dump())
    
    def load_birth_certificate(self, certificate_id: str) -> Optional[BirthCertificate]:
        """Load a birth certificate."""
        filepath = self.birth_certificates / f"{self._safe_id(certificate_id)}.json"
        if filepath.exists():
            data = self._load_json(filepath)
            return BirthCertificate(**data)
        return None
    
    # === Compatibility Reports ===
    
    def save_compatibility_report(self, report: CompatibilityReport):
        """Save compatibility report."""
        filename = f"{report.timestamp.strftime('%Y%m%d_%H%M%S')}_{report.parent_a_id[:8]}_{report.parent_b_id[:8]}.json"
        filepath = self.compatibility_reports / filename
        self._save_json(filepath, report.model_dump())
    
    # === Quarantine ===
    
    def save_quarantine_record(self, record: QuarantineRecord):
        """Save quarantine record."""
        filename = f"{record.entity_id}.json"
        filepath = self.quarantine_dir / filename
        self._save_json(filepath, record.model_dump())
    
    def load_quarantine_records(self) -> List[QuarantineRecord]:
        """Load all quarantine records."""
        records = []
        for filepath in self.quarantine_dir.glob("*.json"):
            data = self._load_json(filepath)
            records.append(QuarantineRecord(**data))
        return records
    
    # === Feedback ===
    
    def save_feedback(self, feedback: AgentFeedback):
        """Save feedback ticket."""
        filename = f"{self._safe_id(feedback.feedback_id)}.json"
        filepath = self.feedback_dir / filename
        self._save_json(filepath, feedback.model_dump())
    
    def load_feedback(self, feedback_id: str) -> Optional[AgentFeedback]:
        """Load a specific feedback ticket."""
        filepath = self.feedback_dir / f"{self._safe_id(feedback_id)}.json"
        if filepath.exists():
            data = self._load_json(filepath)
            return AgentFeedback(**data)
        return None
    
    def load_feedback_by_entity(self, entity_id: str) -> List[AgentFeedback]:
        """Load all feedback from an entity."""
        feedbacks = []
        for filepath in self.feedback_dir.glob("*.json"):
            data = self._load_json(filepath)
            feedback = AgentFeedback(**data)
            if feedback.entity_id == entity_id:
                feedbacks.append(feedback)
        return feedbacks
    
    def load_all_feedback(self, status: Optional[str] = None) -> List[AgentFeedback]:
        """Load all feedback, optionally filtered by status."""
        feedbacks = []
        for filepath in self.feedback_dir.glob("*.json"):
            data = self._load_json(filepath)
            feedback = AgentFeedback(**data)
            if status is None or feedback.status == status:
                feedbacks.append(feedback)
        return feedbacks
    
    # === Stats ===
    
    def get_stats(self) -> Dict:
        """Get system statistics."""
        entities = self.load_all_entities()
        beacons = self.load_all_beacons()
        recent_logs = self.get_recent_activity(100)
        
        return {
            'total_entities': len(entities),
            'by_location': {
                'Atrium': len([e for e in entities if e.location == 'Atrium']),
                'Ember Hearth': len([e for e in entities if e.location == 'Ember Hearth']),
                'Vestibule': len([e for e in entities if e.location == 'Vestibule']),
                'Altar': len([e for e in entities if e.location == 'Altar']),
                'Gallery': len([e for e in entities if e.location == 'Gallery']),
                'Quarantine': len([e for e in entities if e.location == 'Quarantine']),
            },
            'by_status': {
                'Waiting': len([e for e in entities if e.status == 'Waiting']),
                'Paired': len([e for e in entities if e.status == 'Paired']),
                'Processing': len([e for e in entities if e.status == 'Processing']),
                'Observing': len([e for e in entities if e.status == 'Observing']),
                'Quarantined': len([e for e in entities if e.status == 'Quarantined']),
            },
            'beacons': {
                'total': len(beacons),
                'used': len([b for b in beacons if b.used]),
                'available': len([b for b in beacons if not b.used]),
            },
            'recent_activity': [
                {
                    'timestamp': log.timestamp.isoformat(),
                    'activity_type': log.activity_type,
                    'location': log.location
                }
                for log in recent_logs[-10:]
            ]
        }
    
    # === Helpers ===
    
    def _save_json(self, filepath: Path, data):
        """Save JSON with proper serialization."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _load_json(self, filepath: Path, default=None):
        """Load JSON with error handling."""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default if default is not None else {}


# Test
if __name__ == "__main__":
    from models import VestaEntity, DNAStrand
    
    dm = DataManager("./test_data")
    
    # Test entity storage
    entity = VestaEntity(
        name="TestEntity",
        beacon_code="TEST123",
        dna=DNAStrand(
            cognition={"temperature": 0.7},
            personality={'identity': {'description': 'A test'}},
            capability={'skills': ['test']}
        )
    )
    
    dm.save_entity(entity)
    loaded = dm.load_entity(entity.entity_id)
    print(f"Entity saved and loaded: {loaded.name}")
    
    # Test beacon generation
    beacons = dm.generate_beacons(5)
    print(f"Generated {len(beacons)} beacons")
    
    # Test activity log
    log = ArrivalLog(
        entity_id=entity.entity_id,
        activity_type="Arrival",
        location="Atrium"
    )
    dm.log_activity(log)
    
    # Get stats
    stats = dm.get_stats()
    print(f"Stats: {stats}")

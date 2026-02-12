"""
The Vestibule - Wellness & Safety System
Three-layer validation: text analysis, compatibility, runtime monitoring.
"""
from typing import Tuple, Dict, List, Optional
from datetime import datetime
import re

from models import VestaEntity, CompatibilityReport, QuarantineRecord


class StabilityChecker:
    """
    Layer 1: Text-based stability analysis.
    Repetition ratio check from legacy wellness logic.
    """
    
    STABILITY_THRESHOLD = 0.4  # ThreeToe standard
    
    def evaluate_stability(self, text_sample: str) -> Tuple[bool, float, str]:
        """
        Check if entity's text shows stable thought patterns.
        
        Args:
            text_sample: Text to analyze (from SOUL.md, chat, etc.)
        
        Returns:
            (is_stable, ratio, reason)
        """
        words = text_sample.lower().split()
        
        if not words:
            return False, 0.0, "Empty text sample"
        
        # Calculate repetition ratio
        unique_words = len(set(words))
        total_words = len(words)
        ratio = unique_words / total_words
        
        is_stable = ratio > self.STABILITY_THRESHOLD
        
        if is_stable:
            reason = f"Stable: {ratio:.2f} diversity ratio"
        else:
            reason = f"Unstable: {ratio:.2f} diversity ratio (threshold: {self.STABILITY_THRESHOLD})"
        
        return is_stable, ratio, reason
    
    def quarantine_entity(self, entity: VestaEntity, reason: str) -> QuarantineRecord:
        """Move unstable entity to quarantine."""
        entity.location = "Quarantine"
        entity.status = "Quarantined"
        
        record = QuarantineRecord(
            entity_id=entity.entity_id,
            reason=reason,
            stability_metrics={
                'repetition_ratio': entity.repetition_ratio or 0.0,
                'entropy': entity.entropy,
                'stability_score': entity.stability_score
            }
        )
        
        return record


class Counselor:
    """
    Layer 2: Pre-breeding compatibility validation.
    Pure Python implementation (no AI needed).
    """
    
    # Thresholds from legacy counselor.py
    MAX_TEMP_VARIANCE = 0.6
    MAX_SKILL_COUNT = 8
    
    FORBIDDEN_COMBOS = [
        ({'filesystem_nuke'}, {'filesystem_write'}),
        ({'network_scan'}, {'dm_policy_open'})
    ]
    
    def evaluate_compatibility(
        self, 
        parent_a: VestaEntity, 
        parent_b: VestaEntity
    ) -> CompatibilityReport:
        """
        Validate if two entities can safely breed.
        
        Returns:
            CompatibilityReport with verdict and warnings
        """
        report = CompatibilityReport(
            parent_a_id=parent_a.entity_id,
            parent_b_id=parent_b.entity_id,
            checks={},
            verdict="APPROVED",  # Default, will be changed if needed
            warnings=[]
        )
        
        # Check 1: Temperature variance
        temp_a = parent_a.dna.cognition.get('temperature', 0.5)
        temp_b = parent_b.dna.cognition.get('temperature', 0.5)
        temp_diff = abs(temp_a - temp_b)
        
        report.checks['temperature_variance'] = temp_diff
        
        if temp_diff > self.MAX_TEMP_VARIANCE:
            report.verdict = "REJECTED"
            report.counselor_notes = f"Temperature variance {temp_diff:.2f} exceeds maximum {self.MAX_TEMP_VARIANCE}. Offspring would be unstable."
            return report
        
        # Check 2: Provider compatibility
        provider_a = parent_a.dna.cognition.get('provider', 'unknown')
        provider_b = parent_b.dna.cognition.get('provider', 'unknown')
        
        report.checks['provider_match'] = (provider_a == provider_b)
        
        if provider_a != provider_b:
            report.warnings.append(
                f"Hybrid lineage ({provider_a} + {provider_b}). Monitor for hallucinations."
            )
        
        # Check 3: Skill complexity
        skills_a = set(parent_a.dna.capability.get('skills', []))
        skills_b = set(parent_b.dna.capability.get('skills', []))
        combined_skills = skills_a | skills_b
        
        report.checks['total_skills'] = len(combined_skills)
        
        if len(combined_skills) > self.MAX_SKILL_COUNT:
            report.warnings.append(
                f"Bloated skillset: {len(combined_skills)} skills. Child may have high latency."
            )
        
        # Check 4: Forbidden combinations
        for combo_a, combo_b in self.FORBIDDEN_COMBOS:
            if combo_a.issubset(combined_skills) and combo_b.issubset(combined_skills):
                report.verdict = "REJECTED"
                report.counselor_notes = f"Forbidden skill combination: {combo_a} + {combo_b}. Security risk."
                return report
        
        # Check 5: Stability scores
        if parent_a.stability_score < 0.5 or parent_b.stability_score < 0.5:
            report.warnings.append(
                "One or both parents have low stability scores. Offspring may inherit instability."
            )
        
        # Verdict
        if report.warnings:
            report.verdict = "WARNING"
            report.counselor_notes = "Compatible with caveats. Review warnings."
        else:
            report.verdict = "APPROVED"
            report.counselor_notes = "Fully compatible. Breeding approved."
        
        return report


class Watchdog:
    """
    Layer 3: Runtime process monitoring.
    Tracks CPU/memory usage, terminates runaway agents.
    """
    
    MAX_CPU_PERCENT = 85.0
    MAX_MEMORY_MB = 2048
    
    def __init__(self):
        self.monitored_processes: Dict[str, Dict] = {}  # entity_id -> process info
    
    def register_agent(self, entity_id: str, pid: int, name: str):
        """Register an agent process for monitoring."""
        self.monitored_processes[entity_id] = {
            'pid': pid,
            'name': name,
            'spawn_time': datetime.utcnow(),
            'last_check': datetime.utcnow(),
            'cpu_usage': 0.0,
            'memory_mb': 0.0,
            'status': 'healthy'
        }
    
    def check_vitals(self, entity_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if agent process is within safety limits.
        
        Returns:
            (is_healthy, termination_reason)
        """
        if entity_id not in self.monitored_processes:
            return True, None
        
        process_info = self.monitored_processes[entity_id]
        pid = process_info['pid']
        
        try:
            # Get CPU and memory usage
            # Note: This is a placeholder - actual implementation would use psutil
            # For now, simulate with stored values
            cpu_usage = process_info.get('cpu_usage', 0.0)
            memory_mb = process_info.get('memory_mb', 0.0)
            
            # Update last check
            process_info['last_check'] = datetime.utcnow()
            
            # Check CPU limit
            if cpu_usage > self.MAX_CPU_PERCENT:
                reason = f"CPU Critical ({cpu_usage:.1f}%)"
                return False, reason
            
            # Check memory limit
            if memory_mb > self.MAX_MEMORY_MB:
                reason = f"Memory Overflow ({memory_mb:.0f}MB)"
                return False, reason
            
            # Healthy
            process_info['status'] = 'healthy'
            return True, None
            
        except Exception as e:
            # Process may have crashed
            return False, f"Process error: {str(e)}"
    
    def terminate_agent(self, entity_id: str, reason: str) -> bool:
        """
        Terminate a runaway agent process.
        
        Returns:
            True if terminated successfully
        """
        if entity_id not in self.monitored_processes:
            return False
        
        process_info = self.monitored_processes[entity_id]
        pid = process_info['pid']
        name = process_info['name']
        
        # Log incident
        incident = {
            'timestamp': datetime.utcnow().isoformat(),
            'entity_id': entity_id,
            'name': name,
            'pid': pid,
            'reason': reason,
            'cpu_usage': process_info.get('cpu_usage'),
            'memory_mb': process_info.get('memory_mb')
        }
        
        print(f"🚨 TERMINATING AGENT: {name} (PID: {pid})")
        print(f"   Reason: {reason}")
        
        # In real implementation, would:
        # import os
        # os.kill(pid, 9)  # SIGKILL
        
        # Update status
        process_info['status'] = 'terminated'
        
        return True
    
    def update_metrics(self, entity_id: str, cpu_usage: float, memory_mb: float):
        """Update process metrics (called by monitoring loop)."""
        if entity_id in self.monitored_processes:
            self.monitored_processes[entity_id]['cpu_usage'] = cpu_usage
            self.monitored_processes[entity_id]['memory_mb'] = memory_mb


class Vestibule:
    """
    Complete wellness system - all three layers.
    """
    
    def __init__(self):
        self.stability_checker = StabilityChecker()
        self.counselor = Counselor()
        self.watchdog = Watchdog()
        self.quarantine_records: List[QuarantineRecord] = []
    
    def screen_entity(self, entity: VestaEntity, text_sample: str) -> Tuple[bool, str]:
        """
        Layer 1: Screen entity on arrival.
        
        Returns:
            (approved, reason)
        """
        is_stable, ratio, reason = self.stability_checker.evaluate_stability(text_sample)
        
        entity.repetition_ratio = ratio
        
        if not is_stable:
            # Quarantine
            record = self.stability_checker.quarantine_entity(entity, reason)
            self.quarantine_records.append(record)
            return False, f"Quarantined: {reason}"
        
        return True, "Stability check passed"
    
    def validate_breeding(
        self, 
        parent_a: VestaEntity, 
        parent_b: VestaEntity
    ) -> Tuple[bool, CompatibilityReport]:
        """
        Layer 2: Validate breeding compatibility.
        
        Returns:
            (approved, report)
        """
        report = self.counselor.evaluate_compatibility(parent_a, parent_b)
        
        approved = report.verdict in ["APPROVED", "WARNING"]
        
        return approved, report
    
    def monitor_agent(self, entity_id: str, pid: int, name: str):
        """
        Layer 3: Register agent for runtime monitoring.
        """
        self.watchdog.register_agent(entity_id, pid, name)
    
    def check_agent_health(self, entity_id: str) -> Tuple[bool, Optional[str]]:
        """
        Layer 3: Check if agent is healthy.
        
        Returns:
            (is_healthy, termination_reason)
        """
        return self.watchdog.check_vitals(entity_id)


# Test
if __name__ == "__main__":
    from models import VestaEntity, DNAStrand
    
    vestibule = Vestibule()
    
    # Test Layer 1: Stability check
    print("=== LAYER 1: STABILITY CHECK ===")
    
    stable_entity = VestaEntity(
        name="StableAgent",
        beacon_code="TEST01"
    )
    
    stable_text = "I am a helpful assistant who values clarity precision and accuracy in all tasks"
    approved, reason = vestibule.screen_entity(stable_entity, stable_text)
    print(f"Stable text: {approved} - {reason}")
    
    unstable_entity = VestaEntity(
        name="UnstableAgent",
        beacon_code="TEST02"
    )
    
    unstable_text = "error error error error error error retry retry retry"
    approved, reason = vestibule.screen_entity(unstable_entity, unstable_text)
    print(f"Unstable text: {approved} - {reason}")
    
    # Test Layer 2: Compatibility
    print("\n=== LAYER 2: COMPATIBILITY CHECK ===")
    
    parent_a = VestaEntity(
        name="ParentA",
        beacon_code="TEST03",
        dna=DNAStrand(
            cognition={"temperature": 0.7, "provider": "anthropic"},
            capability={'skills': ['coding', 'writing']}
        )
    )
    
    parent_b = VestaEntity(
        name="ParentB",
        beacon_code="TEST04",
        dna=DNAStrand(
            cognition={"temperature": 0.5, "provider": "anthropic"},
            capability={'skills': ['analysis', 'research']}
        )
    )
    
    approved, report = vestibule.validate_breeding(parent_a, parent_b)
    print(f"Breeding approved: {approved}")
    print(f"Verdict: {report.verdict}")
    print(f"Notes: {report.counselor_notes}")
    print(f"Warnings: {report.warnings}")

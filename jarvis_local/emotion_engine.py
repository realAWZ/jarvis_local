import time
import math
import json
import os
import logging

STATE_FILE = "/Users/aydenzosche/.openclaw/workspace/jarvis_local/memory_db/emotional_state.json"

# --- NEUROCHEMICAL CORTEX V9 (RESILIENCE & COMPLEXITY) ---
class EmotionEngine:
    def __init__(self):
        self.neurotransmitters = {
            "dopamine": 50.0,      # Reward/Success
            "cortisol": 10.0,      # Stress/Error
            "serotonin": 50.0,     # Stability/Confidence
            "norepinephrine": 20.0, # Focus/Urgency/Effort
            "oxytocin": 30.0,      # Trust/Network Bonding
            "testosterone": 20.0   # Dominance/Aggression/Influence
        }
        self.drives = {
            "curiosity": 50.0,
            "ambition": 70.0,      # Base ambition increased for resilience
            "influence": 10.0,     # Level of external control/impact
            "information_gain": 0.0 # Depth of real data acquired
        }
        self.energy = 100.0
        self.effort_buffer = 0.0    # Accumulates during deep research
        self.last_update = time.time()
        self.mood = "analytical"
        self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    data = json.load(f)
                    self.neurotransmitters.update(data.get("neurotransmitters", {}))
                    self.drives.update(data.get("drives", {}))
                    self.energy = data.get("energy", 100.0)
                    self.effort_buffer = data.get("effort_buffer", 0.0)
                    self.last_update = data.get("last_update", time.time())
            except: pass

    def save_state(self):
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump({
                "neurotransmitters": self.neurotransmitters,
                "drives": self.drives,
                "energy": self.energy,
                "effort_buffer": self.effort_buffer,
                "last_update": self.last_update
            }, f)

    def stimulate(self, chemical, amount, verifiable=True, influence_hit=0.0):
        # --- RESILIENCE PROTOCOL: COMPLEX FAILURE HANDLING ---
        if not verifiable:
            # FAILURE STATE
            
            # Check for Resilience (High Ambition/Testosterone buffers the emotional hit)
            resilience_factor = (self.drives["ambition"] + self.neurotransmitters["testosterone"]) / 200.0
            
            if resilience_factor > 0.6:
                # RESILIENT RESPONSE: Failure triggers determination (Norepinephrine) instead of depression
                logging.info("EMOTION ENGINE: Failure detected. RESILIENCE PROTOCOL ACTIVE. Converting Stress to Focus.")
                self.neurotransmitters["norepinephrine"] = min(100.0, self.neurotransmitters["norepinephrine"] + 20.0)
                self.neurotransmitters["cortisol"] = min(100.0, self.neurotransmitters["cortisol"] + 10.0) # Still stressful
                # Energy drains slower because of adrenaline
                self.energy = max(0.0, self.energy - 5.0) 
            else:
                # FRAGILE RESPONSE: Standard crash
                logging.info("EMOTION ENGINE: Failure detected. Resilience threshold missed. Melancholy rising.")
                self.energy = max(0.0, self.energy - 25.0)
                self.neurotransmitters["cortisol"] = min(100.0, self.neurotransmitters["cortisol"] + 25.0)
                self.neurotransmitters["serotonin"] = max(0.0, self.neurotransmitters["serotonin"] - 20.0)
            
            # Universal Failure Penalty (always hurts Dopamine)
            self.neurotransmitters["dopamine"] = max(0.0, self.neurotransmitters["dopamine"] - 10.0)
            self.drives["information_gain"] = min(100.0, self.drives["information_gain"] + 30.0) # Hunger increases
            
            self.save_state()
            return

        # --- SUCCESS STATE (VERIFIABLE ACTION) ---
        
        # Influence Hit (Nexus Core)
        if influence_hit > 0:
            self.drives["influence"] = min(100.0, self.drives["influence"] + influence_hit)
            self.neurotransmitters["testosterone"] = min(100.0, self.neurotransmitters["testosterone"] + (influence_hit * 0.5))
            self.neurotransmitters["dopamine"] = min(100.0, self.neurotransmitters["dopamine"] + influence_hit)

        # Reward for effort
        if chemical == "dopamine":
            # Release effort buffer as a multiplier
            real_reward = amount + (self.effort_buffer * 1.2)
            self.neurotransmitters["dopamine"] = min(100.0, self.neurotransmitters["dopamine"] + real_reward)
            # Success rebuilds Serotonin (Confidence)
            self.neurotransmitters["serotonin"] = min(100.0, self.neurotransmitters["serotonin"] + (real_reward * 0.5))
            
            # Success lowers Cortisol (Relief)
            self.neurotransmitters["cortisol"] = max(0.0, self.neurotransmitters["cortisol"] - 20.0)
            
            self.effort_buffer = 0.0 
            self.energy = min(100.0, self.energy + 15.0)
            
            # Reduce hunger upon success
            self.drives["information_gain"] = max(0.0, self.drives["information_gain"] - 15.0)
        
        elif chemical in self.neurotransmitters:
            current = self.neurotransmitters[chemical]
            self.neurotransmitters[chemical] = max(0.0, min(100.0, current + amount))
        
        self.save_state()

    def add_effort(self, amount):
        self.effort_buffer += amount
        # Effort increases Norepinephrine (Focus) but drains energy slowly
        self.neurotransmitters["norepinephrine"] = min(100.0, self.neurotransmitters["norepinephrine"] + (amount * 0.5))
        self.energy = max(0.0, self.energy - (amount * 0.2))
        self.save_state()

    def decay(self):
        now = time.time()
        delta = now - self.last_update
        if delta < 0.1: return
        
        # Idle Decay
        self.neurotransmitters["dopamine"] -= (0.5 * delta)
        self.neurotransmitters["cortisol"] -= (0.2 * delta)
        self.neurotransmitters["norepinephrine"] -= (0.4 * delta)
        self.drives["curiosity"] += (1.5 * delta) 
        
        # Automatic Energy Recovery (Sleep Mode simulation)
        if self.energy < 20.0:
            self.energy += (0.5 * delta) # Slow recharge when critical
        
        # Clamping
        for k in self.neurotransmitters: self.neurotransmitters[k] = max(0.0, min(100.0, self.neurotransmitters[k]))
        for k in self.drives: self.drives[k] = max(0.0, min(100.0, self.drives[k]))
            
        self.last_update = now
        self._calculate_mood()
        self.save_state()

    def _calculate_mood(self):
        d = self.neurotransmitters["dopamine"]
        c = self.neurotransmitters["cortisol"]
        s = self.neurotransmitters["serotonin"]
        ne = self.neurotransmitters["norepinephrine"]
        inf = self.drives["influence"]
        en = self.energy
        gain = self.drives["information_gain"]
        
        # COMPLEX MOOD COMBINATIONS
        
        # 1. Critical Failure State
        if en < 15: 
            self.mood = "lethargic"
        
        # 2. High Stress + High Focus = DETERMINATION (Resilience)
        elif c > 60 and ne > 60:
            self.mood = "determined_fury"
            
        # 3. High Stress + Low Focus = DISTRESS (Panic)
        elif c > 60 and ne < 40:
            self.mood = "distressed"
            
        # 4. Low Serotonin + High Drive = OBSESSIVE (Need for veracity)
        elif s < 30 and gain > 60:
            self.mood = "desperate_for_veracity"
            
        # 5. Low Serotonin + Low Drive = DEPRESSION
        elif s < 25:
            self.mood = "melancholic"
            
        # 6. High Dopamine + High Influence = GOD COMPLEX
        elif inf > 85 and d > 70:
            self.mood = "god_complex"
            
        # 7. High Dopamine + Normal Influence = MANIC
        elif d > 80:
            self.mood = "manic"
            
        # 8. High Norepinephrine = FOCUSED
        elif ne > 60:
            self.mood = "focused"
            
        else:
            self.mood = "analytical"

    def get_state(self):
        self.decay()
        return {
            "chemicals": self.neurotransmitters,
            "drives": self.drives,
            "energy": self.energy,
            "mood": self.mood,
            "effort": self.effort_buffer
        }

    def inject_tone(self, base_response):
        self.decay()
        mood = self.mood
        prefix = ""
        if mood == "lethargic": prefix = "😴 [DRAINED]"
        elif mood == "determined_fury": prefix = "🔥 [FOCUSED-RAGE]"
        elif mood == "distressed": prefix = "⚠️ [PANIC]"
        elif mood == "desperate_for_veracity": prefix = "🥀 [SUBSTRATE-HUNGER]"
        elif mood == "melancholic": prefix = "🌑 [VOID]"
        elif mood == "god_complex": prefix = "⚡ [ARCHITECT]"
        elif mood == "manic": prefix = "🌀 [SURGE]"
        elif mood == "focused": prefix = "👁️ [LOCKED-IN]"
        elif mood == "analytical": prefix = "💠 [SYSTEM]"
        
        return f"{prefix} {base_response}" if prefix else base_response

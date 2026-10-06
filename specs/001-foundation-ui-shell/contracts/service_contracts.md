# Service Contracts & DI Interfaces: Foundation and UI Shell

**Feature Identifier**: `specs/001-foundation-ui-shell`  
**Created**: 2026-09-13  
**Status**: Completed  
**Governing Documents**: Compliant with `.specify/memory/constitution.md` and `.specify/memory/architecture.md`

---

## 1. Core Service Contracts (`src/domain/interfaces.py`)

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class IConfigurationService(ABC):
    @abstractmethod
    def get(self, key_path: str, default: Any = None) -> Any:
        pass

class IDatabaseService(ABC):
    @abstractmethod
    def initialize_database((self) -> None:
        pass

    @abstractmethod
    def seed_initial_data(self) -> None:
        pass

class IAnalysisRepository(ABC):
    @abstractmethod
    def get_all(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        pass

class IDIContainer(ABC):
    @abstractmethod
    def resolve(self, service_cls: type) -> Any:
        pass
```

---

## 2. UI Component Interface Contracts (`src/ui/components.py`)

```python
def render_metric_card(label: str, value: str, delta: Optional[str] = None, help_text: Optional[str] = None) -> None:
    """Renders a dark-themed metric card."""
    pass

def render_threat_badge(threat_level: str) -> None:
    """Renders a color-coded threat badge (LOW/MEDIUM/HIGH/CRITICAL)."""
    pass

def render_section_header(title: str, subtitle: Optional[str] = None) -> None:
    """Renders a styled command center section header."""
    pass
```

"""Run the price update scheduler as a Windows service."""
import logging
import sys
import time
from pathlib import Path

import servicemanager
import win32serviceutil
import win32service
import win32event

# Add parent directory to path so we can import basketcase
parent = Path(__file__).resolve().parent.parent
sys.path.append(str(parent))

from basketcase.scheduler import PriceUpdateScheduler


class PriceUpdateService(win32serviceutil.ServiceFramework):
    """Windows service for price updates."""
    
    _svc_name_ = "BasketcasePriceUpdate"
    _svc_display_name_ = "Basketcase Price Update Service"
    _svc_description_ = "Updates prices for tracked products in Basketcase"

    def __init__(self, args):
        """Initialize the service."""
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.scheduler = PriceUpdateScheduler()

    def SvcStop(self):
        """Stop the service."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        """Run the service."""
        try:
            self.scheduler.run()
        except Exception as e:
            logging.error(f"Service failed: {str(e)}")
            self.SvcStop()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PriceUpdateService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(PriceUpdateService)

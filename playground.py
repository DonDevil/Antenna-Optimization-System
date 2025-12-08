'''
from ai_core.ai_core_manager import AICoreManager
ai_mgr = AICoreManager()
params = ai_mgr.predict_inverse("patch_rect", 2.4, 100)          # inverse suggestion
fwd = ai_mgr.predict_forward("patch_rect", params)             # forward estimate
opt = ai_mgr.optimize_parameters("patch_rect", 2.4, 100) 
print("----------------------------------------------------------------------------------------------------------------------------")
print(f"Inverse('patch rectangular', 2.4, 100) : {params} \nnForward ('patch rectangular', params): {fwd}\nOptimized('patch rectangular', 2.4, 100) : {opt}")
print("----------------------------------------------------------------------------------------------------------------------------")'''
'''
from cst_interface.cst_driver import CSTDriver

cst = CSTDriver()
r = cst.extract_s11_results(r"E:\Final Year Project\antenna\2.4- planar.cst")
print(r)'''

from cst.interface import DesignEnvironment
import cst.results

de = DesignEnvironment()

cst_file = r"E:\Final Year Project\antenna\2.4- planar.cst" # replace with actual path on your machine
mws = de.new_mws()
mws.save(path = r'E:\Antenna Optimization System\cst_interface\output\my_file.cst', include_results = True, allow_overwrite = True)
de.close()
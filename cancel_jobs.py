import kcomposer.KBDr.kcomposer as kcomp
import os

session = kcomp.KBDrSession(os.getenv("KBDR_RUNNER_API_BASE_URL"), timeout=10)

start = 35605
end = 35721

# 00008b15
# 00008b89

for idx in range(start,end+1) :
    final_id = "0000" + str(hex(idx))[2:]
    print(final_id)
    try :
        session.abort_job(final_id)
    except Exception as e :
        continue
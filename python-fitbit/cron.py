from crontab import CronTab
#init cron
cron   = CronTab()

#add new cron job
job  = cron.new(command='echo ho')

#job settings
job.minute.every(1)

job_standard_output = job.run()

for job in cron:
    print job

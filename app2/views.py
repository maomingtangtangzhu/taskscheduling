from django.shortcuts import render
from .models import Host,User,Record,Method
from django.views import generic
import paramiko
import time
# Create your views here.
from django.http import HttpResponse

def index(request):
    num_hosts=Host.objects.all().count()
    num_records=Record.objects.all().count()
    return render(request,'index.html',context={'num_hosts':num_hosts,'num_records':num_records,})

class HostListView(generic.ListView):
    model = Host
    template_name='hosts/list.html'

class RecordListView(generic.ListView):
    model = Record 
    template_name='records/list.html'

def StepView(request):
    return render(request,'steps/list.html')

def StepResultView(request):
    if request.method == "POST":
        ip = request.POST.get("ip")
        username = request.POST.get("username")
        command = request.POST.get("command")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip,22,username,'dsq',timeout=5)
        shell=ssh.invoke_shell()
        time.sleep(0.1)

        shell.send('su - \n')
        buff=''
        while not buff.endswith('Password: '):
            resp=shell.recv(10000)
            buff+=resp.decode('utf-8')
            print("buff:"+buff)
        shell.send('dsq\n')
        buff=''
        while not buff.endswith('# '):
            resp=shell.recv(10000)
            buff+=resp.decode('utf-8')
        print("root reach")

        shell.send('rm -f /tmp/test \n')
        shell.close()
        ssh.close()
        response = ip+":"+username+":"+command+":"+buff
        return HttpResponse(response)
    else:
        return HttpResponse("wrong request")

def FlowView(request):
    method_list=Method.objects.all()
    context={"method_list":method_list}
    return render(request,'flows/list.html',context)

def FlowCommitView(request):
    if request.method == "POST":
        mid = int(request.POST.get("fcb"))
        print("mid=%d"%(mid))
        obj = Method.objects.get(id=mid)
        ip = obj.ip.ip
        username = obj.username.username
        command = obj.command
        print("%s:%s:%s"%(ip,username,command))
        password = User.objects.filter(ip__ip=ip,username=username)[0].password
        print("%s"%password)
        if username !='root':
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip,22,username,password,timeout=5)
            stdin,stdout,stderr = ssh.exec_command(command)
            out,err=stdout.read().decode('utf-8'),stderr.read().decode('utf-8')
            status=stdout.channel.recv_exit_status()
            return HttpResponse(out+":"+err+":status=%d"%status)
        else:
            return HttpResponse(ip+":"+username+":"+command)

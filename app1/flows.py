from viewflow import this
from viewflow.workflow import flow, lock, act
from viewflow.workflow.flow import views

from .models import  HelloWorldProcess

class HelloWorldFlow(flow.Flow):
    process_class = HelloWorldProcess

    start = (
        flow.Start(views.CreateProcessView.as_view(fields=["text"]))
        .Annotation(title="New message")
        .Permission(auto_create=True)
        .Next(this.approve)
    )

    approve = (
        flow.View(views.UpdateProcessView.as_view(fields=["approved"]))
        .Permission(auto_create=True)
        .Next(this.check_approve)
    )

    check_approve = (
        flow.If(act.process.approved)
        .Then(this.send)
        .Else(this.end)
    )

    send = (
        flow.Function(this.send_hello_world_request)
        .Next(this.end)
    )

    end = flow.End()

    def send_hello_world_request(self, activation):
        print(activation.process.text)
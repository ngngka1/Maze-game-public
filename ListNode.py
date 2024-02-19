class ListNode:
    def __init__(self, val=None, next=None, prev=None) -> None:
        self.val = val
        self.prev = prev
        self.next = next
        
    def __iter__(self):
        if self:
            while self and (self.val is not None):
                yield self.val
                self = self.next
        else:
            return []
    
    def nodes(self):
        if self:
            while self and (self.val is not None):
                yield self
                self = self.next
        else:
            return []
    
    @staticmethod
    def append_linkedlist(object, head, tail) -> tuple:
        if head.val is None: # if the list is not created yet
            head.val = object
            tail = head
        else:
            if not tail.prev:
                head.next = ListNode(object, None, head)
                tail = head.next
            else:
                tail.next = ListNode(object, None, tail)
                tail = tail.next
        return tail
                    
    @staticmethod
    def pop(head: "ListNode"):
        if head.prev:
            head.prev.next = head.next
        elif head.next:
            head.val = head.next.val
            head.next = head.next.next
            if head.next:
                head.next.prev = head # Reasigning the prev pointer for the next next node
        else:
            head.val = None

        
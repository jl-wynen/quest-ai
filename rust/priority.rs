use std::cmp::Ordering;
use std::collections::BinaryHeap;

/**
 * Priority queue that uses costs instead of priorities.
 * The cost may be floating point in which case the queue pretends that
 * NaN's don't exist. If a cost is NaN, the behaviour is undefined.
 */
pub struct PriorityQueue<T, C> {
    heap: BinaryHeap<PriorityQueueNode<T, C>>,
}

impl<T, C> PriorityQueue<T, C>
where
    T: PartialEq,
    C: PartialEq + PartialOrd + Copy,
{
    pub fn new() -> Self {
        Self {
            heap: BinaryHeap::new(),
        }
    }

    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            heap: BinaryHeap::with_capacity(capacity),
        }
    }

    pub fn is_empty(&self) -> bool {
        self.heap.is_empty()
    }

    pub fn push(&mut self, value: T, cost: C) {
        self.heap.push(PriorityQueueNode { value, cost });
    }

    pub fn pop(&mut self) -> Option<T> {
        self.heap.pop().map(|node| node.value)
    }

    pub fn clear(&mut self) {
        self.heap.clear();
    }
}

#[derive(PartialEq)]
struct PriorityQueueNode<T, C> {
    cost: C,
    value: T,
}

// Ignore the possibility of NaN's.
impl<T, C> Eq for PriorityQueueNode<T, C>
where
    T: PartialEq,
    C: PartialEq + PartialOrd,
{
}

impl<T, C> PartialOrd for PriorityQueueNode<T, C>
where
    T: PartialEq,
    C: PartialEq + PartialOrd + Copy,
{
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl<T, C> Ord for PriorityQueueNode<T, C>
where
    T: PartialEq,
    C: PartialEq + PartialOrd + Copy,
{
    fn cmp(&self, other: &Self) -> Ordering {
        // Compare self and other in reverse order to produce a min-heap.
        //
        // Break ties in cost by comparing values.
        // Since values cannot be ordered, only compare for equality
        // and assume that the other's cost is greater to prefer self over other.
        compare_cost(other.cost, self.cost).then_with(|| {
            if self.value == other.value {
                Ordering::Equal
            } else {
                Ordering::Greater
            }
        })
    }
}

fn compare_cost<C: PartialEq + PartialOrd>(a: C, b: C) -> Ordering {
    if a == b {
        Ordering::Equal
    } else if a < b {
        Ordering::Less
    } else {
        // If either is NaN, we just assume that the new cost is greater.
        Ordering::Greater
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_makes_empty_queue() {
        let queue: PriorityQueue<i32, i32> = PriorityQueue::new();
        assert!(queue.is_empty());
    }

    #[test]
    fn can_pop_pushed_element() {
        let mut queue = PriorityQueue::new();
        queue.push(12, 51.2);
        assert_eq!(queue.pop(), Some(12));
    }

    #[test]
    fn pop_removes_element() {
        let mut queue = PriorityQueue::new();
        queue.push(12, 51.2);
        queue.pop();
        assert!(queue.is_empty());
    }

    #[test]
    fn pop_with_empty_queue_returns_none() {
        let mut queue: PriorityQueue<i32, i32> = PriorityQueue::new();
        assert_eq!(queue.pop(), None);
    }

    #[test]
    fn pop_returns_element_with_lowest_cost() {
        let mut queue = PriorityQueue::new();
        queue.push("a", 1.3);
        queue.push("b", 0.12);
        queue.push("c", 3.1);
        assert_eq!(queue.pop(), Some("b"));
        assert_eq!(queue.pop(), Some("a"));
        assert_eq!(queue.pop(), Some("c"));
    }

    #[test]
    fn clear_makes_queue_empty() {
        let mut queue = PriorityQueue::new();
        queue.push("a", 1.3);
        assert!(!queue.is_empty());
        queue.clear();
        assert!(queue.is_empty());
    }
}

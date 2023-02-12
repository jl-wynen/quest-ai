use crate::path::theta_star::ThetaStar;
use crate::priority::PriorityQueue;
use crate::world::{to_grid_pos, GridPos, World};
use nalgebra as na;
use pyo3::prelude::*;

type Coord = i64;
type Pos = na::Point2<Coord>;

#[allow(unused)]
fn euclidean_distance(a: &Pos, b: &Pos) -> f64 {
    use nalgebra::Norm;
    let diff = a - b;
    na::EuclideanNorm {}.norm(&na::Vector2::new(diff.x as f64, diff.y as f64))
}

#[allow(unused)]
fn manhattan_distance(a: &Pos, b: &Pos) -> i64 {
    (a - b).sum()
}

#[pyclass]
struct Path {
    target: Pos,
    path: Vec<Pos>,
    pathfinder: ThetaStar,
}

impl Path {
    fn next_impl(&mut self, current: &Pos, world: &World, speed: f64, dt: f64) -> Option<&Pos> {
        if current == &self.target {
            return None;
        }
        if self.path.is_empty() {
            self.find_path(current, world, speed, dt);
        }
        self.drop_until_not_at(current);
        self.path.last()
    }

    fn drop_until_not_at(&mut self, pos: &Pos) {
        while let Some(top) = self.path.last() {
            if top == pos {
                self.path.pop();
            } else {
                break;
            }
        }
    }

    fn find_path(&mut self, start: &Pos, world: &World, speed: f64, dt: f64) {
        match self.pathfinder.find_path(start, &self.target, world) {
            None => {}
            Some(path) => {
                self.path = path;
            }
        }
    }
}

#[pymethods]
impl Path {
    #[new]
    fn new() -> Self {
        Self {
            target: Pos::origin(),
            path: Vec::with_capacity(32),
            pathfinder: ThetaStar::new(),
        }
    }

    fn set_target(&mut self, target: (Coord, Coord)) {
        self.target = Pos::new(target.0, target.1);
        self.clear_path();
    }

    fn next(
        &mut self,
        current: (Coord, Coord),
        world: &World,
        speed: f64,
        dt: f64,
    ) -> Option<(Coord, Coord)> {
        self.next_impl(&Pos::new(current.0, current.1), world, speed, dt)
            .map(|p| (p.x, p.y))
    }

    fn clear_path(&mut self) {
        self.path.clear();
    }
}

pub fn bind(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<Path>()?;
    Ok(())
}

mod theta_star {
    use super::*;
    use std::collections::HashMap;

    pub struct ThetaStar {
        /// Unexpanded nodes.
        /// value: node
        /// cost: cost to go to node + heuristic
        open_set: PriorityQueue<Pos, f64>,
        /// Maps node to its parent
        parents: HashMap<Pos, Pos>,
        /// Current best cost to go to node
        costs: HashMap<Pos, f64>,
    }

    impl ThetaStar {
        pub fn new() -> Self {
            Self {
                open_set: PriorityQueue::with_capacity(64),
                parents: HashMap::with_capacity(32),
                costs: HashMap::with_capacity(64),
            }
        }

        pub fn clear(&mut self) {
            self.open_set.clear();
            self.parents.clear();
            self.costs.clear();
        }

        pub fn find_path(&mut self, start: &Pos, target: &Pos, world: &World) -> Option<Vec<Pos>> {
            if !world.in_bounds(&to_grid_pos(*target)) {
                println!("Cannot find path, target is out of bounds: {target}");
                return None;
            }

            println!("start search {:?} -> {:?}", start, target);
            self.clear();
            self.open_set.push(*start, 0.0);
            self.costs.insert(*start, 0.0);

            while let Some(current) = self.open_set.pop() {
                if target == &current {
                    break;
                }

                for neighbour in world
                    .free_neighbours_of(&to_grid_pos(current))
                    .map(|n| Pos::new(n.x as Coord, n.y as Coord))
                {
                    let src = self.source_of(&neighbour, &current, world);
                    if neighbour == src {
                        continue;
                    }

                    let cost = self.costs[&src] + euclidean_distance(&src, &neighbour);
                    if cost < *self.costs.get(&neighbour).unwrap_or(&f64::INFINITY) {
                        let expected_cost = cost + euclidean_distance(&neighbour, target);
                        self.open_set.push(neighbour, expected_cost);
                        self.parents.insert(neighbour, src);
                        self.costs.insert(neighbour, cost);
                    }
                }
            }
            println!("search done");

            if !self.parents.contains_key(target) {
                println!("Failed to find path");
                return None;
            }

            Some(self.reconstruct_path(start, target))
        }

        fn source_of(&self, node: &Pos, current: &Pos, world: &World) -> Pos {
            if self.parents.contains_key(current)
                && !bresenham::path_is_blocked(&self.parents[current], node, world)
            {
                self.parents[current]
            } else {
                *current
            }
        }

        fn reconstruct_path(&self, start: &Pos, target: &Pos) -> Vec<Pos> {
            let mut path = Vec::with_capacity(32);
            let mut curr = *target;
            while curr != *start {
                path.push(curr);
                curr = self.parents[&curr];
            }
            path.push(*start);
            println!("found path {:?}", path);
            path
        }
    }
}

// Collision detection based on Bresenham's line drawing algorithm.
mod bresenham {
    use super::*;

    type SGridPos = na::Point2<isize>;

    pub fn path_is_blocked(p0: &Pos, p1: &Pos, world: &World) -> bool {
        let d = p1 - p0;
        if d.x.abs() > d.y.abs() {
            let (p0, p1) = if p0.x > p1.x { (p1, p0) } else { (p0, p1) };
            path_is_blocked_low(snap_to_grid(p0), snap_to_grid(p1), world)
        } else {
            let (p0, p1) = if p0.y > p1.y { (p1, p0) } else { (p0, p1) };
            path_is_blocked_high(snap_to_grid(p0), snap_to_grid(p1), world)
        }
    }

    /// For dx > dy
    fn path_is_blocked_low(p0: SGridPos, p1: SGridPos, world: &World) -> bool {
        let diff = p1 - p0;
        let dx = diff.x;
        let dy = diff.y.abs();
        let mut d = 2 * dy - dx;
        let y_increment: isize = if p0.y > p1.y { -1 } else { 1 };

        let mut y = p0.y;
        for x in p0.x..(p1.x + 1) {
            if world.is_obstacle(new_grid_pos(x, y)) {
                return true;
            }
            if d > 0 {
                y += y_increment;
                d += 2 * (dy - dx);
            } else {
                d += 2 * dy;
            }
        }
        false
    }

    /// For dy > dx
    fn path_is_blocked_high(p0: SGridPos, p1: SGridPos, world: &World) -> bool {
        let diff = p1 - p0;
        let dx = diff.x.abs();
        let dy = diff.y;
        let mut d = 2 * dx - dy;
        let x_increment: isize = if p0.x > p1.x { -1 } else { 1 };

        let mut x = p0.x;
        for y in p0.y..(p1.y + 1) {
            if world.is_obstacle(new_grid_pos(x, y)) {
                return true;
            }
            if d > 0 {
                x += x_increment;
                d += 2 * (dx - dy);
            } else {
                d += 2 * dx;
            }
        }
        false
    }

    fn snap_to_grid(pos: &Pos) -> SGridPos {
        SGridPos::new(pos.x as isize, pos.y as isize)
    }

    fn new_grid_pos(x: isize, y: isize) -> GridPos {
        GridPos::new(x as usize, y as usize)
    }
}

use crate::world::{to_grid_pos, GridPos, World};
use nalgebra as na;
use pyo3::prelude::*;
use std::collections::{BinaryHeap, HashMap};

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

#[derive(PartialEq, Eq)]
struct Cell {
    cost: i64,
    value: Pos,
}

impl PartialOrd for Cell {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Cell {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        other.cost.cmp(&self.cost)
    }
}

#[pyclass]
struct Path {
    target: Pos,
    path: Vec<Pos>,
    open_set: BinaryHeap<Cell>,
    parents: HashMap<Pos, Pos>,
    costs: HashMap<Pos, i64>,
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
        if !world.in_bounds(&to_grid_pos(self.target)) {
            println!("Cannot find path, target is out of bounds: {}", self.target);
            return;
        }

        println!("start search {:?} -> {:?}", start, self.target);
        self.clear_path();
        self.open_set.push(Cell {
            value: *start,
            cost: 0,
        });
        self.costs.insert(*start, 0);
        let end = self.target;

        while let Some(Cell {
            value: current,
            cost: _,
        }) = self.open_set.pop()
        {
            if &self.target == &current {
                break;
            }

            for neighbour in world.free_neighbours_of(&to_grid_pos(current)) {
                let neighbour = Pos::new(neighbour.x as Coord, neighbour.y as Coord);
                let new_cost = self.costs[&current] + 1;
                let next_cost = self.costs.get(&neighbour);
                if next_cost.is_none() || new_cost < *next_cost.unwrap() {
                    self.costs.insert(neighbour, new_cost);
                    let priority = new_cost + manhattan_distance(&neighbour, &end);
                    self.open_set.push(Cell {
                        value: neighbour,
                        cost: priority,
                    });
                    self.parents.insert(neighbour, current);
                }
            }
        }

        if !self.parents.contains_key(&end) {
            println!("Failed to find path");
            return;
        }

        let mut curr = end;
        while curr != *start {
            self.path.push(curr);
            curr = self.parents[&curr];
        }

        self.path.push(*start);

        println!("found path {:?}", self.path);
        self.smooth_path(world);
        println!("smoothed   {:?}", self.path);
    }

    fn smooth_path(&mut self, world: &World) {
        if self.path.len() < 3 {
            return;
        }
        let mut a = *self.path.last().unwrap();
        for i in (0..self.path.len() - 2).rev() {
            let b = self.path[i];
            if bresenham::path_is_blocked(&a, &b, world) {
                a = b;
            } else {
                self.path.remove(i + 1);
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
            open_set: BinaryHeap::with_capacity(64),
            parents: HashMap::with_capacity(32),
            costs: HashMap::with_capacity(64),
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
        self.open_set.clear();
        self.parents.clear();
        self.costs.clear();
    }
}

pub fn bind(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<Path>()?;
    Ok(())
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
            if world.is_obstacle(new_grid_pos(x, y - 1))
                || world.is_obstacle(new_grid_pos(x, y))
                || world.is_obstacle(new_grid_pos(x, y + 1))
            {
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
            if world.is_obstacle(new_grid_pos(x - 1, y))
                || world.is_obstacle(new_grid_pos(x, y))
                || world.is_obstacle(new_grid_pos(x + 1, y))
            {
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

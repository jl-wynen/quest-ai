use crate::world::{GridPos, World};
use approx::AbsDiffEq;
use nalgebra as na;
use pyo3::prelude::*;
use std::collections::{BinaryHeap, HashMap};

type WorldCoord = f64;
type WorldPos = na::Point2<WorldCoord>;
type Coord = i32;
type Pos = na::Point2<Coord>;

// Treat positions as equal if they are within epsilon of each other.
const EPSILON: f64 = 1.0;

fn as_world_pos<T: na::Scalar + Into<WorldCoord> + Copy>(pos: &na::Point2<T>) -> WorldPos {
    WorldPos::new(pos.x.into(), pos.y.into())
}

fn snap_to_grid(pos: &WorldPos) -> Pos {
    Pos::new(pos.x as Coord, pos.y as Coord)
}

/// Euclidean
// fn distance(a: WorldPos, b: WorldPos) -> f64 {
//     use nalgebra::Norm;
//     na::EuclideanNorm{}.norm(&(a-b))
// }

/// Manhattan
fn distance(a: &Pos, b: &Pos) -> i32 {
    (a - b).sum()
}

fn are_close<T: na::Scalar + Into<WorldCoord> + Copy>(p0: &WorldPos, p1: &na::Point2<T>) -> bool {
    // use approx::AbsDiffEq;
    p0.abs_diff_eq(&as_world_pos(p1), EPSILON)
}

#[derive(PartialEq, Eq)]
struct Cell {
    cost: i32,
    value: Pos,
}

impl PartialOrd for Cell {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Cell {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.cost.cmp(&other.cost)
    }
}
//
// impl PartialEq for Cell {
//     fn eq(&self, other: &Self) -> bool {
//         self.cost == other.cost && are_close(&self.value, &other.value)
//     }
// }

// impl Eq for Cell {}

#[pyclass]
struct Path {
    target: WorldPos,
    path: Vec<Pos>,
    open_set: BinaryHeap<Cell>,
    parents: HashMap<Pos, Pos>,
    costs: HashMap<Pos, i32>,
}

impl Path {
    fn next_impl(&mut self, current: &Pos, world: &World, dt: f64) -> Option<&Pos> {
        if are_close(&self.target, current) {
            return None;
        }
        if self.path.is_empty() {
            self.find_path(current, world, dt);
        }
        self.drop_until_not_at(current);
        self.path.first()
    }

    fn drop_until_not_at(&mut self, pos: &Pos) {
        while let Some(top) = self.path.first() {
            if top == pos {
                self.path.pop();
            } else {
                break;
            }
        }
    }

    fn find_path(&mut self, start: &Pos, world: &World, dt: f64) {
        println!("start search {:?} {:?}", start, self.target);
        self.clear_path();
        self.open_set.push(Cell {
            value: *start,
            cost: 0,
        });
        self.costs.insert(*start, 0);
        let end = snap_to_grid(&self.target);

        while let Some(Cell {
            value: current,
            cost: _,
        }) = self.open_set.pop()
        {
            if are_close(&self.target, &current) {
                break;
            }

            for neighbour in
                world.free_neighbours_of(&GridPos::new(current.x as usize, current.y as usize))
            {
                let neighbour = Pos::new(neighbour.x as Coord, neighbour.y as Coord);
                let new_cost = self.costs[&current] + 1;
                let next_cost = self.costs.get(&neighbour);
                if next_cost.is_none() || new_cost < *next_cost.unwrap() {
                    self.costs.insert(neighbour, new_cost);
                    let priority = new_cost + distance(&neighbour, &end);
                    self.open_set.push(Cell {
                        value: neighbour,
                        cost: priority,
                    });
                    self.parents.insert(neighbour, current);
                }
            }
        }

        if !self.parents.contains_key(&end) {
            return;
        }

        let mut curr = end;
        while !curr.eq(&start) {
            self.path.push(curr);
            curr = self.parents[&curr];
        }

        self.path.push(*start);
        self.path.reverse();

        println!("found path {:?}", self.path);
    }

    fn clear_path(&mut self) {
        self.path.clear();
        self.open_set.clear();
        self.parents.clear();
        self.costs.clear();
    }
}

#[pymethods]
impl Path {
    #[new]
    fn new() -> Self {
        Self {
            target: WorldPos::origin(),
            path: Vec::with_capacity(32),
            open_set: BinaryHeap::with_capacity(64),
            parents: HashMap::with_capacity(32),
            costs: HashMap::with_capacity(64),
        }
    }

    fn set_target(&mut self, target: (WorldCoord, WorldCoord)) {
        self.target = WorldPos::new(target.0, target.1);
        self.clear_path();
    }

    fn next(
        &mut self,
        current: (WorldCoord, WorldCoord),
        world: &World,
        dt: f64,
    ) -> Option<(WorldCoord, WorldCoord)> {
        self.next_impl(&Pos::new(current.0 as Coord, current.1 as Coord), world, dt)
            .map(|p| (p.x as WorldCoord, p.y as WorldCoord))
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

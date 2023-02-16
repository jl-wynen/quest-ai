extern crate janlukas;
use janlukas::path::Path;
use janlukas::world::World;

fn main() {
    let world = World::new((1000, 1000));
    let mut path = Path::new(&world);
    for i in 10..90 {
        path.set_target((900.0, 10.0 * i as f64));
        let _ = path.next((4.0, 4.0), &world, 1.0, 1.0 / 30.0);
    }
}

/*
Results:

theta*
Benchmark 1: target/release/path_on_empty_grid
  Time (mean ± σ):     652.8 ms ±  12.9 ms    [User: 642.4 ms, System: 9.6 ms]
  Range (min … max):   643.7 ms … 684.9 ms    10 runs

 A*
 Benchmark 1: target/release/path_on_empty_grid
  Time (mean ± σ):     348.2 ms ±   4.8 ms    [User: 341.3 ms, System: 6.2 ms]
  Range (min … max):   341.3 ms … 355.7 ms    10 runs

*/

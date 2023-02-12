#![allow(non_snake_case)]

mod path;
mod pos;
mod pos_map;
mod priority;
mod world;

use pyo3::prelude::*;

#[pymodule]
fn _janlukas(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    world::bind(py, m)?;
    path::bind(py, m)?;
    Ok(())
}

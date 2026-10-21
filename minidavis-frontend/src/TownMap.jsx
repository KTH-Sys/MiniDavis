import { GRID_SIZE, residents as defaultResidents, RESIDENT_COLORS } from './data';

// Size of each grid tile in pixels
const TILE = 48;

/**
 * TownMap Component
 *
 * Renders a 12x12 grid of tiles with resident markers overlaid.
 * Accepts `residents` array as a prop, falling back to defaultResidents from data.js.
 */
function TownMap({ residents = defaultResidents }) {
  // Total pixel dimensions for the 12x12 grid (12 * 48 = 576px)
  const mapSize = GRID_SIZE * TILE;

  // Create an array with 144 items (12 * 12) to render each grid tile
  const tiles = Array.from({ length: GRID_SIZE * GRID_SIZE });

  return (
    // Map container: relative positioning allows resident markers to be positioned
    // absolutely relative to the top-left (0, 0) of the grid.
    <div
      style={{
        position: 'relative',
        width: `${mapSize}px`,
        height: `${mapSize}px`,
        margin: '0 auto',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
        borderRadius: '8px',
        overflow: 'hidden',
      }}
    >
      {/* Tile Grid: 12x12 grid rendered using CSS Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${GRID_SIZE}, ${TILE}px)`,
          gridTemplateRows: `repeat(${GRID_SIZE}, ${TILE}px)`,
          width: `${mapSize}px`,
          height: `${mapSize}px`,
        }}
      >
        {tiles.map((_, index) => (
          <div
            key={index}
            style={{
              width: `${TILE}px`,
              height: `${TILE}px`,
              backgroundColor: '#d8f3dc', // Light green background
              border: '1px solid #d1d5db', // Thin gray border
              boxSizing: 'border-box',
            }}
          />
        ))}
      </div>

      {/* Residents: Drawn on top of the grid, absolutely positioned at (x * TILE, y * TILE) */}
      {residents.map((resident) => {
        // Resolve color from resident object or lookup table
        const color = resident.color || RESIDENT_COLORS[resident.id] || '#457b9d';

        return (
          <div
            key={resident.id}
            title={`${resident.name} (${resident.x}, ${resident.y})`}
            style={{
              position: 'absolute',
              left: `${resident.x * TILE}px`,
              top: `${resident.y * TILE}px`,
              width: `${TILE}px`,
              height: `${TILE}px`,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'left 0.3s ease, top 0.3s ease', // Smooth movement between tiles
            }}
          >
            {/* Colored circle using the resident's assigned color */}
            <div
              style={{
                width: `${TILE * 0.5}px`,
                height: `${TILE * 0.5}px`,
                borderRadius: '50%',
                backgroundColor: color,
                border: '2px solid #ffffff',
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.25)',
                boxSizing: 'border-box',
              }}
            />

            {/* Small text label displaying the resident's name underneath */}
            <span
              style={{
                fontSize: '10px',
                fontWeight: 600,
                color: '#1b4332',
                marginTop: '2px',
                lineHeight: 1,
                userSelect: 'none',
                textShadow: '0 0 2px rgba(255, 255, 255, 0.8)',
              }}
            >
              {resident.name}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export default TownMap;

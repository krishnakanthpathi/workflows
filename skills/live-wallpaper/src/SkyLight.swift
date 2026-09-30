import Cocoa
import CoreFoundation

// MARK: - SkyLight Private CGS Spaces API

typealias CGSConnectionIDFunc = @convention(c) () -> Int32
typealias CGSCopySpacesFunc = @convention(c) (Int32) -> Unmanaged<CFArray>?
typealias CGSAddWindowsToSpacesFunc = @convention(c) (Int32, CFArray, CFArray) -> Void
typealias CGSRemoveWindowsFromSpacesFunc = @convention(c) (Int32, CFArray, CFArray) -> Void

var cgsConnection: CGSConnectionIDFunc?
var copyManagedSpaces: CGSCopySpacesFunc?
var addWindowsToSpaces: CGSAddWindowsToSpacesFunc?
var removeWindowsFromSpaces: CGSRemoveWindowsFromSpacesFunc?

func initSkyLight() {
    guard let handle = dlopen("/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight", RTLD_LAZY) else {
        return
    }
    if let symConn = dlsym(handle, "CGSMainConnectionID") {
        cgsConnection = unsafeBitCast(symConn, to: CGSConnectionIDFunc.self)
    }
    if let symSpaces = dlsym(handle, "CGSCopyManagedDisplaySpaces") {
        copyManagedSpaces = unsafeBitCast(symSpaces, to: CGSCopySpacesFunc.self)
    }
    if let symAdd = dlsym(handle, "CGSAddWindowsToSpaces") {
        addWindowsToSpaces = unsafeBitCast(symAdd, to: CGSAddWindowsToSpacesFunc.self)
    }
    if let symRemove = dlsym(handle, "CGSRemoveWindowsFromSpaces") {
        removeWindowsFromSpaces = unsafeBitCast(symRemove, to: CGSRemoveWindowsFromSpacesFunc.self)
    }
}

func getAllSpaceIDs() -> [Int64] {
    if cgsConnection == nil { initSkyLight() }
    guard let getCID = cgsConnection, let getSpaces = copyManagedSpaces else { return [] }
    let cid = getCID()
    guard let unmanaged = getSpaces(cid) else { return [] }
    let array = unmanaged.takeRetainedValue() as [AnyObject]
    guard let monitor = array.first as? [String: Any],
          let spaces = monitor["Spaces"] as? [[String: Any]] else {
        return []
    }
    return spaces.compactMap { $0["id64"] as? Int64 }
}

func getCurrentSpaceIndex() -> Int {
    if cgsConnection == nil { initSkyLight() }
    guard let getCID = cgsConnection, let getSpaces = copyManagedSpaces else { return 0 }
    let cid = getCID()
    guard let unmanaged = getSpaces(cid) else { return 0 }
    let array = unmanaged.takeRetainedValue() as [AnyObject]
    guard let monitor = array.first as? [String: Any],
          let cur = monitor["Current Space"] as? [String: Any],
          let curId = cur["ManagedSpaceID"] as? Int,
          let spaces = monitor["Spaces"] as? [[String: Any]] else {
        return 0
    }
    let ids = spaces.compactMap { $0["ManagedSpaceID"] as? Int }
    if let idx = ids.firstIndex(of: curId) {
        return idx
    }
    return 0
}

func pinWindowToSpace(windowNumber: Int, spaceID: Int64, allSpaceIDs: [Int64]) {
    if cgsConnection == nil { initSkyLight() }
    guard let getCID = cgsConnection,
          let add = addWindowsToSpaces,
          let remove = removeWindowsFromSpaces else { return }
    let cid = getCID()
    remove(cid, [windowNumber] as CFArray, allSpaceIDs as CFArray)
    add(cid, [windowNumber] as CFArray, [spaceID] as CFArray)
}
